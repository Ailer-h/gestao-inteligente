import os

import psycopg
from fastapi import HTTPException
from psycopg.rows import dict_row

import config  # Carrega o .env da raiz antes de ler as configurações.


def get_connection():
    database_url = os.getenv('DATABASE_URL', '').strip()
    if not database_url:
        raise HTTPException(status_code=503, detail='DATABASE_URL não configurada.')
    try:
        with psycopg.connect(
            database_url, connect_timeout=10, sslmode='require', row_factory=dict_row
        ) as connection:
            yield connection
    except psycopg.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail='Dados duplicados, vínculo inválido ou registro vinculado a outro cadastro.',
        ) from error
    except psycopg.OperationalError as error:
        raise HTTPException(status_code=503, detail='Banco de dados indisponível.') from error
