import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from fastapi.testclient import TestClient

from app.agents import OPERATOR_PROMPT
from app.config import OLLAMA_MODEL
from app.main import app


class OperatorTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Mock only the network boundary to cover the complete request flow.
        self.network_patch = patch("app.ollama.urlopen")
        self.urlopen = self.network_patch.start()
        self.addCleanup(self.network_patch.stop)
        self.addCleanup(self.client.close)

    def ollama_response(self, payload):
        response = self.urlopen.return_value.__enter__.return_value
        response.read.return_value = json.dumps(payload).encode("utf-8")

    def post_message(self):
        return self.client.post("/api/agents/operator/chat", json={"message": "hi"})

    def test_chat_sends_operator_prompt_and_returns_reply(self):
        self.ollama_response({"message": {"content": "  How can I help?  "}})
        response = self.client.post(
            "/api/agents/operator/chat", json={"message": "  Help with deliveries  "}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "agent": "operator", "reply": "How can I help?", "model": OLLAMA_MODEL
        })
        request = self.urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(payload["model"], OLLAMA_MODEL)
        self.assertFalse(payload["stream"])
        self.assertFalse(payload["think"])
        self.assertEqual(payload["messages"], [
            {"role": "system", "content": OPERATOR_PROMPT},
            {"role": "user", "content": "Help with deliveries"},
        ])
        self.assertNotIn("tools", payload)

    def test_invalid_requests_do_not_contact_ollama(self):
        for payload in (
            {}, {"message": ""}, {"message": " \n\t "}, {"message": 123},
            {"message": None}, {"message": "a" * 8001},
            {"message": "hello", "agent": "inventory"},
        ):
            with self.subTest(payload=repr(payload)[:100]):
                response = self.client.post("/api/agents/operator/chat", json=payload)
                self.assertEqual(response.status_code, 422)
                self.assertIn("detail", response.json())
        response = self.client.post(
            "/api/agents/operator/chat", content="{",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 422)
        self.urlopen.assert_not_called()

    def test_inventory_is_not_exposed(self):
        response = self.client.post("/api/agents/inventory/chat", json={"message": "hi"})
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("/api/agents/{agent}/chat", app.openapi()["paths"])
        self.urlopen.assert_not_called()

    def test_unavailable_ollama_returns_recovery_guidance(self):
        self.urlopen.side_effect = URLError("Connection refused")
        response = self.post_message()
        self.assertEqual(response.status_code, 503)
        self.assertIn("Start Ollama", response.json()["detail"])

    def test_missing_model_returns_recovery_guidance(self):
        self.urlopen.side_effect = HTTPError(
            "http://localhost:11434/api/chat", 404, "Not Found", {}, io.BytesIO(b"")
        )
        response = self.post_message()
        self.assertEqual(response.status_code, 503)
        self.assertIn(f"ollama pull {OLLAMA_MODEL}", response.json()["detail"])

    def test_timeout_returns_clear_error(self):
        self.urlopen.side_effect = TimeoutError()
        response = self.post_message()
        self.assertEqual(response.status_code, 504)
        self.assertIn("120 seconds", response.json()["detail"])

    def test_upstream_http_error_does_not_leak_body(self):
        self.urlopen.side_effect = HTTPError(
            "http://localhost:11434/api/chat", 500, "Error", {},
            io.BytesIO(b"private details"),
        )
        response = self.post_message()
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("private details", response.text)

    def test_invalid_upstream_shapes_return_errors(self):
        for payload in ([], None, {}, {"message": None}, {"message": []},
                        {"message": {"content": " "}}, {"message": {"content": 42}}):
            with self.subTest(payload=payload):
                self.ollama_response(payload)
                self.assertEqual(self.post_message().status_code, 502)

    def test_invalid_upstream_json_returns_error(self):
        response = self.urlopen.return_value.__enter__.return_value
        response.read.return_value = b"not json"
        self.assertEqual(self.post_message().status_code, 502)


if __name__ == "__main__":
    unittest.main()
