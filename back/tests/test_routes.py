import asyncio
import json
import unittest
from unittest.mock import MagicMock

from database import get_connection
from main import app
from security import require_user


async def request(method, path, body=None, headers=None):
    messages = []
    payload = json.dumps(body).encode() if body is not None else b''
    received = False

    async def receive():
        nonlocal received
        if not received:
            received = True
            return {'type': 'http.request', 'body': payload, 'more_body': False}
        return {'type': 'http.disconnect'}

    async def send(message):
        messages.append(message)

    await app(
        {
            'type': 'http', 'asgi': {'version': '3.0'}, 'http_version': '1.1',
            'method': method, 'scheme': 'http', 'path': path, 'raw_path': path.encode(),
            'query_string': b'', 'root_path': '',
            'headers': [(b'content-type', b'application/json'), *(headers or [])],
            'client': ('127.0.0.1', 12345), 'server': ('test', 80),
        },
        receive,
        send,
    )
    status = next(item['status'] for item in messages if item['type'] == 'http.response.start')
    content = b''.join(item.get('body', b'') for item in messages if item['type'] == 'http.response.body')
    return status, json.loads(content) if content else None


class RoutesTest(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        app.dependency_overrides[get_connection] = lambda: self.connection
        app.dependency_overrides[require_user] = lambda: {'id': '12345678-1234-1234-1234-123456789abc'}

    def tearDown(self):
        app.dependency_overrides.clear()

    def call(self, method, path, body=None):
        return asyncio.run(request(method, path, body))

    def test_create_resources_and_defaults(self):
        person = {'nome': 'Ana', 'sexo': 'F', 'rg': '123', 'cpf': '12345678901', 'endereco': 'Rua A'}
        cases = [
            ('/atividades', {'nome': 'Oficina'}, {'id': 1, 'nome': 'Oficina', 'tipo_atividade': 3}),
            ('/criancas', {**person, 'frequenta_escola': False}, {**person, 'id': 1, 'frequenta_escola': False}),
            ('/responsaveis', person, {**person, 'id': 1}),
        ]
        for path, body, record in cases:
            with self.subTest(path=path):
                self.connection.execute.return_value.fetchone.return_value = record
                status, content = self.call('POST', path, body)
                self.assertEqual(status, 201)
                self.assertEqual(content['id'], record['id'])
                if path == '/atividades':
                    self.assertEqual(self.connection.execute.call_args.args[1], ('Oficina', None, 3, None))
                if path == '/usuarios':
                    self.assertEqual(content['cargo'], 3)

    def test_partial_update_preserves_omitted_fields(self):
        self.connection.execute.return_value.fetchone.return_value = {'id': 1, 'nome': 'Novo', 'tipo_atividade': 3}
        status, _ = self.call('PATCH', '/atividades/1', {'nome': 'Novo'})
        self.assertEqual(status, 200)
        self.assertEqual(self.connection.execute.call_args.args[1], ('Novo', 1))
        self.assertNotIn('tipo_atividade', self.connection.execute.call_args.args[0].as_string())

    def test_nullable_field_can_be_cleared(self):
        self.connection.execute.return_value.fetchone.return_value = {'id': 1, 'nome': 'Oficina', 'tipo_atividade': 3}
        status, _ = self.call('PATCH', '/atividades/1', {'data': None})
        self.assertEqual(status, 200)
        self.assertEqual(self.connection.execute.call_args.args[1], (None, 1))

    def test_invalid_input_does_not_execute_sql(self):
        cases = [
            ('POST', '/atividades', {'nome': 'Teste', 'tipo_atividade': 4}),
            ('POST', '/criancas', {'nome': 'Teste'}),
            ('PATCH', '/atividades/1', {'nome': None}),
            ('PATCH', '/atividades/1', {'nome': '   '}),
            ('PATCH', '/atividades/1', {'id': 2}),
            ('PATCH', '/atividades/1', {}),
            ('GET', '/usuarios/invalid-uuid', None),
        ]
        for method, path, body in cases:
            with self.subTest(path=path, body=body):
                self.assertEqual(self.call(method, path, body)[0], 422)
        self.connection.execute.assert_not_called()

    def test_missing_record_returns_404(self):
        self.connection.execute.return_value.fetchone.return_value = None
        for method, body in [('GET', None), ('PATCH', {'nome': 'Novo'}), ('DELETE', None)]:
            self.assertEqual(self.call(method, '/atividades/999', body)[0], 404)

    def test_delete_returns_empty_204(self):
        self.connection.execute.return_value.fetchone.return_value = {'id': 1}
        self.assertEqual(self.call('DELETE', '/atividades/1'), (204, None))

    def test_list_and_pagination_defaults(self):
        self.connection.execute.return_value.fetchall.return_value = []
        self.assertEqual(self.call('GET', '/atividades'), (200, []))
        self.assertEqual(self.connection.execute.call_args.args[1], (50, 0))


if __name__ == '__main__':
    unittest.main()
