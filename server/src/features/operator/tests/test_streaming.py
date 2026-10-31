import asyncio
import json
import unittest
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from src.features.operator.runtime import stream_chat
from src.main import app
from tests.support.account_fixture import AccountFixture
from tests.support.runtime_fixture import answer, frame, gateway, stream_response


class StreamingTests(AccountFixture, unittest.TestCase):
    def request(self, upstream):
        with gateway(lambda request: stream_response(upstream)):
            response = self.client.post('/api/agents/operator/chat', json={'message': 'Hi', 'stream': True})
        self.assertEqual(response.status_code, 200)
        return [json.loads(line) for line in response.text.splitlines()]

    def test_session_tokens_and_done(self):
        events = self.request(answer('Hello'))
        self.assertEqual([event['type'] for event in events], ['session', 'token', 'done'])
        self.assertFalse(events[-1]['truncated'])

    def test_reasoning_and_tool_status_are_not_answer_text(self):
        reasoning = 'data: ' + json.dumps({'choices': [{'delta': {'reasoning_content': 'PRIVATE'}, 'finish_reason': None}]}) + '\n\n'
        events = self.request(': keepalive\n\nevent: hermes.tool.progress\ndata: {"private":"TOOL"}\n\n' + reasoning + answer())
        self.assertNotIn('PRIVATE', json.dumps(events))
        self.assertNotIn('TOOL', json.dumps(events))
        self.assertEqual(events[-1]['type'], 'done')

    def test_crlf_multiline_sse(self):
        events = self.request('data: {"choices":\r\ndata: [{"delta":{"content":"Hi"},"finish_reason":"stop"}]}\r\n\r\ndata: [DONE]\r\n\r\n')
        self.assertEqual(events[1]['content'], 'Hi')
        self.assertEqual(events[-1]['type'], 'done')

    def test_malformed_or_incomplete_stream_is_error_not_success(self):
        cases = [
            '', frame('Hi'), frame('Hi') + 'data: [DONE]\n\n',
            frame(finish='stop') + 'data: [DONE]\n\n',
            'data: not json\n\n', 'data: []\n\n', 'data: {"choices":null}\n\n',
            'data: {"choices":[{"delta":[],"finish_reason":null}]}\n\n',
            frame(['bad']), frame('Hi') + frame(finish='error'),
            frame('Hi') + frame(finish='cancelled'), frame('Hi') + frame(finish='tool_calls'),
            frame('Hi', 'stop') + frame('After terminal'),
            frame('Hi') + frame(finish='stop') + 'data: [DONE]',
            'event: approval.request\ndata: {}\n\n',
            'event: unexpected\ndata: {}\n\n',
        ]
        for upstream in cases:
            with self.subTest(upstream=upstream[:100]):
                events = self.request(upstream)
                self.assertEqual(events[-1]['type'], 'error')
                self.assertFalse(any(event['type'] == 'done' for event in events))

    def test_failure_details_are_not_exposed(self):
        events = self.request(frame('Hi') + frame(finish='error', error={'message': 'SECRET'}))
        self.assertEqual(events[-1]['type'], 'error')
        self.assertNotIn('SECRET', json.dumps(events))

    def test_truncated_reply_and_usage_frame(self):
        events = self.request(frame('Partial') + frame(finish='length', error={'message': 'SECRET'}) + 'data: {"choices":[],"usage":{}}\n\ndata: [DONE]\n\n')
        self.assertTrue(events[-1]['truncated'])
        self.assertNotIn('SECRET', json.dumps(events))

    def test_http_error_in_stream_is_an_error_event(self):
        with gateway(lambda request: httpx.Response(401)):
            response = self.client.post('/api/agents/operator/chat', json={'message': 'Hi', 'stream': True})
        self.assertEqual(json.loads(response.text.splitlines()[-1])['type'], 'error')


class GatedStream(httpx.AsyncByteStream):
    def __init__(self):
        self.closed = False
        self.release = asyncio.Event()

    async def __aiter__(self):
        # Deliberately split UTF-8 and SSE across arbitrary network chunks.
        for byte in frame('Halo 👋').encode():
            yield bytes([byte])
        await self.release.wait()
        yield (frame(finish='stop') + 'data: [DONE]\n\n').encode()

    async def aclose(self):
        self.closed = True


class AsyncStreamingTests(unittest.IsolatedAsyncioTestCase):
    async def test_first_token_arrives_before_completion_and_close_reaches_upstream(self):
        upstream = GatedStream()
        with gateway(lambda request: httpx.Response(200, stream=upstream, headers={'content-type': 'text/event-stream'})):
            stream = stream_chat('Instructions', 'Hello', uuid4())
            first = await asyncio.wait_for(anext(stream), timeout=1)
            self.assertEqual(first, {'type': 'token', 'content': 'Halo 👋'})
            self.assertFalse(upstream.release.is_set())
            await stream.aclose()
        self.assertTrue(upstream.closed)

    async def test_cancellation_while_waiting_closes_upstream(self):
        upstream = GatedStream()
        with gateway(lambda request: httpx.Response(200, stream=upstream, headers={'content-type': 'text/event-stream'})):
            stream = stream_chat('Instructions', 'Hello', uuid4())
            await anext(stream)
            pending = asyncio.create_task(anext(stream))
            await asyncio.sleep(0)
            pending.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await pending
        self.assertTrue(upstream.closed)


if __name__ == '__main__':
    unittest.main()
