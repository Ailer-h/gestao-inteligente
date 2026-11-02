import os
from contextlib import asynccontextmanager

import psycopg
from fastapi import HTTPException, Request
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, PoolClosed, PoolTimeout, TooManyRequests
from starlette.concurrency import run_in_threadpool

import config  # Carrega o .env da raiz antes de ler as configurações.


@asynccontextmanager
async def database_lifespan(app):
    database_url = os.getenv('DATABASE_URL', '').strip()
    pool = None
    if database_url:
        pool = ConnectionPool(
            database_url,
            kwargs={'connect_timeout': 10, 'sslmode': 'require', 'row_factory': dict_row},
            min_size=2,
            max_size=5,
            timeout=10,
            max_waiting=20,
            open=False,
        )
        # Workers prepare connections in the background without blocking startup.
        pool.open(wait=False)
    app.state.database_pool = pool
    try:
        yield
    finally:
        app.state.database_pool = None
        if pool is not None:
            await run_in_threadpool(pool.close)


def get_connection(request: Request):
    pool = getattr(request.app.state, 'database_pool', None)
    if pool is None:
        raise HTTPException(status_code=503, detail='DATABASE_URL não configurada.')
    try:
        # Commits/rolls back before returning the connection to the shared pool.
        with pool.connection() as connection:
            yield connection
    except psycopg.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail='Dados duplicados, vínculo inválido ou registro vinculado a outro cadastro.',
        ) from error
    except (psycopg.OperationalError, PoolTimeout, PoolClosed, TooManyRequests) as error:
        raise HTTPException(status_code=503, detail='Banco de dados indisponível.') from error
