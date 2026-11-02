import unittest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from database import get_connection
from main import app
from security import require_user


class FrontIntegrationTest(unittest.TestCase):
    def tearDown(self):
        app.dependency_overrides.clear()

    def test_cors_accepts_vite_authorization_preflight(self):
        with TestClient(app) as client:
            response = client.options('/criancas', headers={
                'Origin': 'http://localhost:5173',
                'Access-Control-Request-Method': 'PATCH',
                'Access-Control-Request-Headers': 'authorization,content-type',
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['access-control-allow-origin'], 'http://localhost:5173')

    def test_cors_rejects_unknown_origin(self):
        with TestClient(app) as client:
            response = client.options('/auth/login', headers={
                'Origin': 'https://unknown.example.com',
                'Access-Control-Request-Method': 'POST',
            })
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('access-control-allow-origin', response.headers)

    def test_summary_returns_all_four_totals(self):
        connection = MagicMock()
        totals = {'criancas': 120, 'responsaveis': 90, 'usuarios': 3, 'atividades': 7}
        connection.execute.return_value.fetchone.return_value = totals
        app.dependency_overrides[get_connection] = lambda: connection
        app.dependency_overrides[require_user] = lambda: {'id': 'test'}
        with TestClient(app) as client:
            response = client.get('/resumo')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), totals)


if __name__ == '__main__':
    unittest.main()
