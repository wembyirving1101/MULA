import time
import unittest
from fastapi.testclient import TestClient
from src.features.auth import accounts
from src.main import app
from tests.support.account_fixture import AccountFixture
from tests.support.runtime_fixture import answer, gateway, stream_response


class AccountTests(AccountFixture, unittest.TestCase):
    def test_unauthenticated_requests_cannot_read_or_chat(self):
        other = TestClient(app)
        self.assertEqual(other.get('/api/conversation').status_code, 401)
        self.assertEqual(other.post('/api/agents/operator/chat', json={'message': 'hi'}).status_code, 401)

    def test_password_hashes_cookie_and_logout_revocation(self):
        token = self.client.cookies.get('mula_session')
        with accounts.database() as db:
            record = db.execute('SELECT * FROM accounts').fetchone()
            self.assertNotEqual(record['password_hash'], 'long-password-123')
            self.assertNotEqual(db.execute('SELECT token_hash FROM sessions').fetchone()[0], token)
        self.client.post('/api/auth/logout')
        old = TestClient(app)
        old.cookies.set('mula_session', token)
        self.assertEqual(old.get('/api/auth/me').status_code, 401)
        response = self.client.post('/api/auth/login', json={'username': 'OWNER', 'password': 'long-password-123'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('HttpOnly', response.headers['set-cookie'])
        self.assertIn('SameSite=strict', response.headers['set-cookie'])
        self.assertEqual(response.json()['conversation_id'], self.account['conversation_id'])
        self.assertNotIn('password_hash', response.json())

    def test_expired_session_is_rejected(self):
        with accounts.database() as db:
            db.execute('UPDATE sessions SET expires = ?', (int(time.time()) - 1,))
        self.assertEqual(self.client.get('/api/auth/me').status_code, 401)

    def test_validation_duplicates_and_login_throttling(self):
        credentials = {'username': 'owner', 'password': 'long-password-123'}
        self.assertEqual(self.client.post('/api/auth/signup', json=credentials).status_code, 409)
        self.assertEqual(self.client.post('/api/auth/signup', json={'username': 'new', 'password': 'short'}).status_code, 422)
        for _ in range(5):
            self.assertEqual(self.client.post('/api/auth/login', json={'username': 'owner', 'password': 'incorrect-password'}).status_code, 401)
        self.assertEqual(self.client.post('/api/auth/login', json=credentials).status_code, 429)

    def test_history_ownership_and_login_continuity(self):
        second = TestClient(app)
        second_account = second.post('/api/auth/signup', json={'username': 'second', 'password': 'another-password'}).json()
        with gateway(lambda request: stream_response(answer('Hello owner'))):
            self.assertEqual(self.client.post('/api/agents/operator/chat', json={'message': 'Private business'}).status_code, 200)
            forbidden = second.post('/api/agents/operator/chat', json={'message': 'hi', 'session_id': self.account['conversation_id']})
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(second.get('/api/conversation').json()['messages'], [])
        saved = self.client.get('/api/conversation').json()
        self.assertEqual([m['text'] for m in saved['messages']], ['Private business', 'Hello owner'])
        self.assertNotEqual(second_account['conversation_id'], saved['session_id'])
        self.client.post('/api/auth/logout')
        self.client.post('/api/auth/login', json={'username': 'owner', 'password': 'long-password-123'})
        self.assertEqual(self.client.get('/api/conversation').json(), saved)

    def test_streamed_reply_is_saved(self):
        with gateway(lambda request: stream_response(answer('Saved stream'))):
            self.client.post('/api/agents/operator/chat', json={'message': 'hello', 'stream': True})
        saved = self.client.get('/api/conversation').json()['messages'][-1]
        self.assertEqual(saved['text'], 'Saved stream')
        self.assertIsNone(saved['note'])
