import asyncio
import os
import unittest
from unittest.mock import MagicMock, patch

import httpx

from database import get_connection
from main import app
from tests.test_routes import request


USER = {'id': '12345678-1234-1234-1234-123456789abc', 'email': 'teste@example.com'}
SESSION = {
    'access_token': 'access-token-de-teste', 'token_type': 'bearer',
    'expires_in': 3600, 'refresh_token': 'refresh-token-de-teste', 'user': USER,
}


class AuthTest(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        self.connection.execute.return_value.fetchone.return_value = USER
        app.dependency_overrides[get_connection] = lambda: self.connection
        self.env = patch.dict(os.environ, {
            'SUPABASE_URL': 'https://example.supabase.co',
            'SUPABASE_ANON_KEY': 'anon-key-de-teste',
        })
        self.env.start()

    def tearDown(self):
        app.dependency_overrides.clear()
        self.env.stop()

    def call(self, method, path, body=None, token=None):
        headers = [(b'authorization', f'Bearer {token}'.encode())] if token else None
        return asyncio.run(request(method, path, body, headers))

    def test_all_business_routes_and_health_require_token(self):
        for path, operations in app.openapi()['paths'].items():
            if path == '/auth/login':
                continue
            path = path.replace('{id}', '1')
            for method in operations:
                with self.subTest(path=path, method=method):
                    status, _ = self.call(method.upper(), path, {})
                    self.assertEqual(status, 401)
        self.connection.execute.assert_not_called()

    @patch('services.auth.httpx.request')
    def test_login_returns_session_without_previous_token(self, remote):
        remote.return_value = httpx.Response(200, json=SESSION)
        status, data = self.call('POST', '/auth/login', {
            'username': ' admin ', 'password': ' senha com espaços ',
        })
        self.assertEqual(status, 200)
        self.assertEqual(data, SESSION)
        self.assertEqual(remote.call_args.args, ('POST', 'https://example.supabase.co/auth/v1/token'))
        self.assertEqual(remote.call_args.kwargs['params'], {'grant_type': 'password'})
        self.assertEqual(remote.call_args.kwargs['json']['password'], ' senha com espaços ')
        self.assertEqual(self.connection.execute.call_args.args[1], ('admin',))
        self.assertEqual(remote.call_args.kwargs['json']['email'], USER['email'])

    @patch('services.auth.httpx.request')
    def test_wrong_password_returns_401_without_upstream_details(self, remote):
        remote.return_value = httpx.Response(400, json={'error_description': 'detalhe interno'})
        status, data = self.call('POST', '/auth/login', {'username': 'admin', 'password': 'errada'})
        self.assertEqual(status, 401)
        self.assertNotIn('detalhe interno', str(data))

    @patch('services.auth.httpx.request')
    def test_unknown_username_returns_generic_401(self, remote):
        self.connection.execute.return_value.fetchone.return_value = None
        status, data = self.call('POST', '/auth/login', {'username': 'inexistente', 'password': 'errada'})
        self.assertEqual(status, 401)
        self.assertEqual(data['detail'], 'Username ou senha inválidos, ou conta indisponível.')
        remote.assert_not_called()

    @patch('services.auth.httpx.request')
    def test_missing_email_does_not_attempt_authentication(self, remote):
        self.connection.execute.return_value.fetchone.return_value = {**USER, 'email': None}
        self.assertEqual(self.call('POST', '/auth/login', {'username': 'admin', 'password': 'senha'})[0], 401)
        remote.assert_not_called()

    @patch('services.auth.httpx.request')
    def test_username_required_and_email_is_not_login_field(self, remote):
        for body in (
            {'email': USER['email'], 'password': 'senha'},
            {'username': '   ', 'password': 'senha'},
            {'username': 'x' * 51, 'password': 'senha'},
        ):
            self.assertEqual(self.call('POST', '/auth/login', body)[0], 422)
        self.connection.execute.assert_not_called()
        remote.assert_not_called()

    @patch('services.auth.httpx.request')
    def test_session_must_belong_to_username_account(self, remote):
        remote.return_value = httpx.Response(200, json={
            **SESSION, 'user': {**USER, 'id': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'},
        })
        self.assertEqual(self.call('POST', '/auth/login', {'username': 'admin', 'password': 'senha'})[0], 401)

    @patch('services.auth.httpx.request')
    def test_valid_token_is_verified_with_supabase(self, remote):
        remote.return_value = httpx.Response(200, json=USER)
        self.connection.execute.return_value.fetchall.return_value = []
        self.assertEqual(self.call('GET', '/atividades', token='token-valido'), (200, []))
        self.assertEqual(remote.call_args.args, ('GET', 'https://example.supabase.co/auth/v1/user'))
        self.assertEqual(remote.call_args.kwargs['headers']['Authorization'], 'Bearer token-valido')
        self.assertEqual(remote.call_args.kwargs['headers']['apikey'], 'anon-key-de-teste')
        self.assertNotIn('json', remote.call_args.kwargs)

    @patch('services.auth.httpx.request')
    def test_invalid_or_expired_token_cannot_reach_database(self, remote):
        for code in (401, 403):
            remote.return_value = httpx.Response(code, json={'msg': 'invalid JWT'})
            self.assertEqual(self.call('GET', '/atividades', token='token-expirado')[0], 401)
        self.connection.execute.assert_not_called()

    @patch('services.auth.httpx.request')
    def test_auth_outage_fails_closed(self, remote):
        remote.side_effect = httpx.ConnectError('offline')
        self.assertEqual(self.call('GET', '/atividades', token='qualquer-token')[0], 503)
        self.connection.execute.assert_not_called()

    @patch('services.auth.httpx.request')
    def test_missing_configuration_fails_closed(self, remote):
        with patch.dict(os.environ, {'SUPABASE_ANON_KEY': ''}):
            self.assertEqual(self.call('GET', '/health', token='qualquer-token')[0], 503)
        remote.assert_not_called()

    @patch('services.auth.httpx.request')
    def test_malformed_auth_response_cannot_authorize(self, remote):
        remote.return_value = httpx.Response(200, json={})
        self.assertEqual(self.call('GET', '/atividades', token='qualquer-token')[0], 401)
        self.connection.execute.assert_not_called()

    def test_openapi_declares_bearer_for_protected_routes(self):
        paths = app.openapi()['paths']
        self.assertNotIn('security', paths['/auth/login']['post'])
        for path, operations in paths.items():
            if path != '/auth/login':
                for operation in operations.values():
                    self.assertEqual(operation['security'], [{'HTTPBearer': []}])


if __name__ == '__main__':
    unittest.main()
