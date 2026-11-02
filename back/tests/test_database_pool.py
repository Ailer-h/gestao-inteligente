import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import psycopg
from fastapi import HTTPException
from psycopg_pool import PoolTimeout

from database import database_lifespan, get_connection


class DatabasePoolTest(unittest.TestCase):
    def test_startup_warms_in_background_and_shutdown_closes(self):
        app = SimpleNamespace(state=SimpleNamespace())

        async def exercise():
            with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://test'}):
                with patch('database.ConnectionPool') as factory:
                    pool = factory.return_value
                    async with database_lifespan(app):
                        self.assertIs(app.state.database_pool, pool)
                        pool.open.assert_called_once_with(wait=False)
                        pool.close.assert_not_called()
                        self.assertEqual(factory.call_args.kwargs['min_size'], 2)
                        self.assertEqual(factory.call_args.kwargs['max_size'], 5)
                    pool.close.assert_called_once()
                    self.assertIsNone(app.state.database_pool)

        asyncio.run(exercise())

    def test_connection_returned_to_pool_on_success_and_error(self):
        pool = MagicMock()
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(database_pool=pool)))
        context = pool.connection.return_value
        context.__exit__.return_value = False
        dependency = get_connection(request)
        self.assertIs(next(dependency), context.__enter__.return_value)
        with self.assertRaises(StopIteration):
            next(dependency)
        context.__exit__.assert_called_once_with(None, None, None)

        context.reset_mock()
        dependency = get_connection(request)
        next(dependency)
        with self.assertRaises(HTTPException) as error:
            dependency.throw(psycopg.IntegrityError('test'))
        self.assertEqual(error.exception.status_code, 409)
        self.assertIs(context.__exit__.call_args.args[0], psycopg.IntegrityError)

    def test_exhausted_pool_returns_503(self):
        pool = MagicMock()
        pool.connection.return_value.__enter__.side_effect = PoolTimeout('test')
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(database_pool=pool)))
        with self.assertRaises(HTTPException) as error:
            next(get_connection(request))
        self.assertEqual(error.exception.status_code, 503)

    def test_missing_configuration_does_not_start_pool(self):
        app = SimpleNamespace(state=SimpleNamespace())

        async def exercise():
            with patch.dict('os.environ', {'DATABASE_URL': ''}):
                with patch('database.ConnectionPool') as factory:
                    async with database_lifespan(app):
                        factory.assert_not_called()
                        with self.assertRaises(HTTPException) as error:
                            next(get_connection(SimpleNamespace(app=app)))
                        self.assertEqual(error.exception.status_code, 503)

        asyncio.run(exercise())
