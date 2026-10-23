import asyncio
import json
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.ollama import OllamaError, stream_chat
from app.config import OLLAMA_KEEP_ALIVE, OLLAMA_NUM_PREDICT


class OllamaStream(httpx.AsyncByteStream):
    def __init__(self, chunks):
        self.chunks = chunks
        self.closed = False

    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk

    async def aclose(self):
        self.closed = True


def encoded_event(content="", done=False, **extra):
    return (json.dumps({
        "message": {"content": content}, "done": done, **extra
    }) + "\n").encode()


class StreamingApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def mock_ollama(self, chunks, status=200):
        self.upstream = OllamaStream(chunks)

        def handler(request):
            payload = json.loads(request.content)
            self.assertTrue(payload["stream"])
            self.assertFalse(payload["think"])
            self.assertEqual(payload["keep_alive"], OLLAMA_KEEP_ALIVE)
            self.assertEqual(payload["options"]["num_predict"], OLLAMA_NUM_PREDICT)
            return httpx.Response(status, stream=self.upstream)

        # Preserve the real client class before replacing the constructor.
        client_class = httpx.AsyncClient
        client_patch = patch(
            "app.ollama.httpx.AsyncClient",
            side_effect=lambda **kwargs: client_class(
                transport=httpx.MockTransport(handler), **kwargs
            ),
        )
        client_patch.start()
        self.addCleanup(client_patch.stop)

    def events(self):
        response = self.client.post(
            "/api/agents/operator/chat", json={"message": "Hello", "stream": True}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/x-ndjson", response.headers["content-type"])
        self.assertEqual(response.headers["x-accel-buffering"], "no")
        return [json.loads(line) for line in response.iter_lines()]

    def test_streams_answer_and_completion_without_thinking(self):
        thinking_chunk = json.dumps({
            "message": {"thinking": "private reasoning", "content": ""}, "done": False
        }).encode() + b"\n"
        self.mock_ollama([
            thinking_chunk, encoded_event("Hello "), encoded_event("there"),
            encoded_event(done=True),
        ])
        self.assertEqual(self.events(), [
            {"type": "token", "content": "Hello "},
            {"type": "token", "content": "there"},
            {"type": "done", "truncated": False},
        ])
        self.assertTrue(self.upstream.closed)

    def test_missing_model_is_clear_stream_error(self):
        self.mock_ollama([], status=404)
        event = self.events()[0]
        self.assertEqual(event["type"], "error")
        self.assertEqual(event["status_code"], 503)
        self.assertIn("ollama pull", event["detail"])

    def test_incomplete_stream_is_not_a_success(self):
        self.mock_ollama([encoded_event("Partial reply")])
        events = self.events()
        self.assertEqual(events[0]["type"], "token")
        self.assertEqual(events[-1]["type"], "error")
        self.assertIn("before finishing", events[-1]["detail"])

    def test_malformed_upstream_is_reported(self):
        self.mock_ollama([b"broken json\n"])
        self.assertEqual(self.events()[0]["status_code"], 502)

    def test_reply_limit_is_reported(self):
        self.mock_ollama([encoded_event("Partial", done=True, done_reason="length")])
        self.assertTrue(self.events()[-1]["truncated"])

    def test_empty_reply_is_reported(self):
        self.mock_ollama([encoded_event(done=True)])
        self.assertEqual(self.events()[-1]["type"], "error")


class IncrementalStreamTests(unittest.IsolatedAsyncioTestCase):
    async def test_first_token_arrives_before_generation_finishes_and_closes_on_stop(self):
        release = asyncio.Event()

        class GatedStream(OllamaStream):
            async def __aiter__(self):
                yield encoded_event("First")
                # If the client buffers everything, the first token cannot arrive.
                await release.wait()
                yield encoded_event(done=True)

        upstream = GatedStream([])
        transport = httpx.MockTransport(
            lambda request: httpx.Response(200, stream=upstream)
        )
        client_class = httpx.AsyncClient
        with patch("app.ollama.httpx.AsyncClient", side_effect=lambda **kwargs:
                   client_class(transport=transport, **kwargs)):
            stream = stream_chat("System prompt", "Hello")
            event = await asyncio.wait_for(anext(stream), timeout=1)
            self.assertEqual(event, {"type": "token", "content": "First"})
            self.assertFalse(release.is_set())
            await stream.aclose()
        self.assertTrue(upstream.closed)

    async def test_connection_failure_is_wrapped(self):
        def fail(request):
            raise httpx.ConnectError("Connection refused", request=request)

        client_class = httpx.AsyncClient
        with patch("app.ollama.httpx.AsyncClient", side_effect=lambda **kwargs:
                   client_class(transport=httpx.MockTransport(fail), **kwargs)):
            with self.assertRaisesRegex(OllamaError, "Start Ollama"):
                await anext(stream_chat("System prompt", "Hello"))
