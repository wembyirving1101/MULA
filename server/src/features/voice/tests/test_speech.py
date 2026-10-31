import asyncio
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.features.voice import service as speech
from src.main import app
from tests.support.account_fixture import AccountFixture


class SpeechEndpointTests(AccountFixture, unittest.TestCase):
    def test_requires_account(self):
        with patch("src.features.voice.service.synthesize", new_callable=AsyncMock) as synthesize:
            self.assertEqual(TestClient(app).post("/api/speech", json={"text": "Hi"}).status_code, 401)
            synthesize.assert_not_awaited()

    def test_validates_input_before_synthesis(self):
        with patch("src.features.voice.service.synthesize", new_callable=AsyncMock) as synthesize:
            for payload in [{}, {"text": " "}, {"text": "a" * 1201}, {"text": 3},
                            {"text": "hello\x00"}, {"text": "hi", "voice": "--help"}]:
                with self.subTest(payload=str(payload)[:50]):
                    self.assertEqual(self.client.post("/api/speech", json=payload).status_code, 422)
            synthesize.assert_not_awaited()

    def test_returns_private_audio_without_adding_chat_messages(self):
        before = self.client.get("/api/conversation").json()
        with patch("src.features.voice.service.synthesize", new_callable=AsyncMock, return_value=b"RIFFaudio") as synthesize:
            response = self.client.post("/api/speech", json={"text": " Hello "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"RIFFaudio")
        self.assertEqual(response.headers["content-type"], "audio/wav")
        self.assertEqual(response.headers["cache-control"], "no-store")
        synthesize.assert_awaited_once_with("Hello")
        self.assertEqual(self.client.get("/api/conversation").json(), before)


class SpeechProviderTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        lock = patch("src.features.voice.service._synthesis_lock", asyncio.Lock())
        lock.start()
        self.addCleanup(lock.stop)

    async def test_no_shell_and_temporary_files_are_removed(self):
        directories = []

        async def launch(*args, **kwargs):
            self.assertEqual(args[0], "/usr/bin/say")
            self.assertNotIn("hello; $(secret)", args)
            source = Path(args[2])
            self.assertEqual(source.read_text(), "hello; $(secret)")
            directories.append(source.parent)
            Path(args[4]).write_bytes(b"RIFF" + bytes(44))
            process = AsyncMock()
            process.returncode = 0
            return process

        with patch("src.features.voice.service.sys.platform", "darwin"), patch("src.features.voice.service.asyncio.create_subprocess_exec", side_effect=launch):
            result = await speech.synthesize("hello; $(secret)")
        self.assertTrue(result.startswith(b"RIFF"))
        self.assertFalse(directories[0].exists())

    async def test_unsupported_platform_has_actionable_failure(self):
        with patch("src.features.voice.service.sys.platform", "linux"):
            with self.assertRaises(HTTPException) as caught:
                await speech.synthesize("hello")
        self.assertEqual(caught.exception.status_code, 503)

    async def test_busy_engine_does_not_queue(self):
        with patch("src.features.voice.service.sys.platform", "darwin"):
            async with speech._synthesis_lock:
                with self.assertRaises(HTTPException) as caught:
                    await speech.synthesize("hello")
        self.assertEqual(caught.exception.status_code, 429)

    async def test_engine_failure_is_sanitized(self):
        process = AsyncMock()
        process.returncode = 1
        with patch("src.features.voice.service.sys.platform", "darwin"), patch(
            "src.features.voice.service.asyncio.create_subprocess_exec", return_value=process
        ):
            with self.assertRaises(HTTPException) as caught:
                await speech.synthesize("private business text")
        self.assertEqual(caught.exception.status_code, 503)
        self.assertNotIn("private business text", caught.exception.detail)

    async def test_timeout_kills_engine_and_releases_capacity(self):
        process = AsyncMock()
        process.returncode = None
        process.kill = unittest.mock.Mock()

        async def timeout(awaitable, **kwargs):
            awaitable.close()
            raise TimeoutError()

        with patch("src.features.voice.service.sys.platform", "darwin"), patch(
            "src.features.voice.service.asyncio.create_subprocess_exec", return_value=process
        ), patch("src.features.voice.service.asyncio.wait_for", side_effect=timeout):
            with self.assertRaises(HTTPException) as caught:
                await speech.synthesize("Hello")
        self.assertEqual(caught.exception.status_code, 504)
        process.kill.assert_called_once()
        self.assertFalse(speech._synthesis_lock.locked())

    async def test_cancellation_kills_process_and_cleans_files(self):
        started = asyncio.Event()
        process = AsyncMock()
        process.returncode = None
        directories = []

        async def wait():
            await asyncio.Event().wait()

        def kill():
            process.returncode = -9
            process.wait.side_effect = None

        process.wait.side_effect = wait
        process.kill = unittest.mock.Mock(side_effect=kill)

        async def launch(*args, **kwargs):
            directories.append(Path(args[2]).parent)
            started.set()
            return process

        with patch("src.features.voice.service.sys.platform", "darwin"), patch("src.features.voice.service.asyncio.create_subprocess_exec", side_effect=launch):
            task = asyncio.create_task(speech.synthesize("hello"))
            await started.wait()
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        process.kill.assert_called_once()
        self.assertFalse(directories[0].exists())
        self.assertFalse(speech._synthesis_lock.locked())


if __name__ == "__main__":
    unittest.main()
