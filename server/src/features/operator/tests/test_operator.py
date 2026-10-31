import json
import unittest
from contextlib import contextmanager
from unittest.mock import patch
from uuid import UUID, uuid4

import httpx
from fastapi.testclient import TestClient

from src.features.operator.agent import OPERATOR_PROMPT
from src.common.config import HERMES_MODEL
from src.main import app
from tests.support.account_fixture import AccountFixture


from tests.support.runtime_fixture import answer, gateway, stream_response


class OperatorTests(AccountFixture, unittest.TestCase):

    def test_request_uses_real_hermes_contract_and_returns_session(self):
        requests = []

        def handler(request):
            requests.append(request)
            return stream_response(answer('Halo 👋'))

        with gateway(handler):
            response = self.client.post('/api/agents/operator/chat', json={'message': '  Hello  '})
        self.assertEqual(response.status_code, 200)
        result = response.json()
        session = UUID(result['session_id'])
        self.assertEqual(result['reply'], 'Halo 👋')
        self.assertEqual(result['agent'], 'operator')
        self.assertEqual(result['model'], HERMES_MODEL)
        self.assertFalse(result['truncated'])
        request = requests[0]
        self.assertEqual(request.url.path, '/v1/chat/completions')
        self.assertEqual(request.headers['Authorization'], 'Bearer test-key')
        self.assertEqual(request.headers['X-Hermes-Session-Id'], f'mula-operator-{session}')
        payload = json.loads(request.content)
        self.assertEqual(payload['messages'], [
            {'role': 'system', 'content': OPERATOR_PROMPT},
            {'role': 'user', 'content': 'Hello'},
        ])
        self.assertTrue(payload['stream'])
        self.assertFalse(payload['model_options']['reasoning']['enabled'])
        self.assertNotIn('tools', payload)

    def test_continuation_reuses_identity_without_replaying_history(self):
        requests = []
        session = self.account["conversation_id"]

        def handler(request):
            requests.append(request)
            return stream_response(answer())

        with gateway(handler):
            for text in ['My shop is Mula Cafe', 'What is my shop called?']:
                result = self.client.post('/api/agents/operator/chat', json={
                    'message': text, 'session_id': session,
                })
                self.assertEqual(result.status_code, 200)
        self.assertEqual(requests[0].headers['X-Hermes-Session-Id'], requests[1].headers['X-Hermes-Session-Id'])
        self.assertEqual(len(json.loads(requests[1].content)['messages']), 2)

    def test_identical_opening_messages_keep_account_conversation(self):
        with gateway(lambda request: stream_response(answer())):
            first = self.client.post('/api/agents/operator/chat', json={'message': 'Hello'}).json()
            second = self.client.post('/api/agents/operator/chat', json={'message': 'Hello'}).json()
        self.assertEqual(first['session_id'], second['session_id'])

    def test_invalid_requests_never_contact_gateway(self):
        invalid = [{}, {'message': ''}, {'message': '   '}, {'message': 3}, {'message': None},
                   {'message': 'a' * 8001}, {'message': 'hi', 'agent': 'inventory'},
                   {'message': 'hi', 'session_id': '../private'},
                   {'message': 'hi', 'session_id': 'bad\r\nAuthorization: Bearer stolen'}]
        with patch('src.features.operator.runtime.httpx.AsyncClient') as client:
            for payload in invalid:
                with self.subTest(payload=str(payload)[:80]):
                    self.assertEqual(self.client.post('/api/agents/operator/chat', json=payload).status_code, 422)
            self.assertEqual(self.client.post('/api/agents/operator/chat', content='{').status_code, 422)
            client.assert_not_called()

    def test_inventory_is_not_claimed_to_exist(self):
        self.assertEqual(self.client.post('/api/agents/inventory/chat', json={'message': 'hi'}).status_code, 404)

    def test_missing_key_fails_without_network(self):
        with patch('src.features.operator.runtime.HERMES_API_KEY', ''), patch('src.features.operator.runtime.httpx.AsyncClient') as client:
            response = self.client.post('/api/agents/operator/chat', json={'message': 'Hi'})
        self.assertEqual(response.status_code, 503)
        client.assert_not_called()

    def test_http_failures_are_sanitized(self):
        for upstream, expected in [(401, 503), (403, 503), (404, 503), (409, 409), (429, 429), (500, 502), (302, 502)]:
            with self.subTest(upstream=upstream), gateway(lambda request: httpx.Response(upstream, text='SECRET')):
                response = self.client.post('/api/agents/operator/chat', json={'message': 'Hi'})
                self.assertEqual(response.status_code, expected)
                self.assertNotIn('SECRET', response.text)

    def test_connection_and_timeout_failures(self):
        for error, status in [(httpx.ConnectError('SECRET'), 503), (httpx.ReadTimeout('SECRET'), 504)]:
            def handler(request):
                raise error
            with self.subTest(error=type(error)), gateway(handler):
                response = self.client.post('/api/agents/operator/chat', json={'message': 'Hi'})
                self.assertEqual(response.status_code, status)
                self.assertNotIn('SECRET', response.text)

    def test_length_limit_is_reported_for_json_too(self):
        with gateway(lambda request: stream_response(answer('Partial', 'length'))):
            response = self.client.post('/api/agents/operator/chat', json={'message': 'Hi'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['truncated'])

    def test_liveness_does_not_claim_gateway_readiness(self):
        with patch('src.features.operator.runtime.httpx.AsyncClient') as client:
            self.assertEqual(self.client.get('/health').json()['runtime'], 'hermes')
            client.assert_not_called()

    def test_readiness_checks_authenticated_hermes_capabilities(self):
        def handler(request):
            self.assertEqual(request.url.path, '/v1/capabilities')
            self.assertEqual(request.headers['Authorization'], 'Bearer test-key')
            return httpx.Response(200, json={'platform': 'hermes-agent', 'features': {'chat_completions': True}})
        with gateway(handler):
            self.assertEqual(self.client.get('/ready').status_code, 200)

    def test_readiness_rejects_non_hermes_or_invalid_payload(self):
        for payload in [{}, [], {'platform': 'ollama'}, {'platform': 'hermes-agent', 'features': {}}]:
            with self.subTest(payload=payload), gateway(lambda request: httpx.Response(200, json=payload)):
                self.assertEqual(self.client.get('/ready').status_code, 503)


if __name__ == '__main__':
    unittest.main()
