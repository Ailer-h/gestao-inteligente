import logging
import os
from uuid import UUID

import httpx
from fastapi import HTTPException
from psycopg import Connection

from repositories import usuario as repository
from schemas.usuario import UsuarioCreate


def admin_request(method: str, path: str, body=None):
    url = os.getenv('SUPABASE_URL', '').strip().rstrip('/')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '').strip()
    if not url or not key:
        raise HTTPException(status_code=503, detail='Cadastro de usuários não configurado no servidor.')
    try:
        response = httpx.request(method, f'{url}/auth/v1/admin/users{path}',
            headers={'apikey': key, 'Authorization': f'Bearer {key}'},
            json=body, timeout=15, follow_redirects=False)
    except httpx.RequestError as error:
        raise HTTPException(status_code=503, detail='Serviço de cadastro indisponível.') from error
    if response.status_code in (400, 422):
        raise HTTPException(status_code=409, detail='Email já cadastrado ou dados recusados pela política de senha.')
    if not response.is_success:
        raise HTTPException(status_code=503, detail='Serviço de cadastro indisponível. Confira a configuração do servidor.')
    if method == 'DELETE':
        return None
    try:
        data = response.json()
        return UUID(data['id'])
    except (ValueError, KeyError, TypeError) as error:
        raise HTTPException(status_code=502, detail='Resposta inválida do serviço de cadastro.') from error


def cadastrar(connection: Connection, body: UsuarioCreate):
    # Verifica duplicidade local antes de criar uma conta externa.
    with connection.transaction():
        if connection.execute(
            'SELECT id FROM public.perfil_usuario WHERE username = %s OR cpf = %s',
            (body.username, body.cpf),
        ).fetchone():
            raise HTTPException(status_code=409, detail='Usuário ou CPF já cadastrado.')
    id = admin_request('POST', '', {
        'email': body.email, 'password': body.password.get_secret_value(), 'email_confirm': True,
    })
    try:
        with connection.transaction():
            return repository.incluir(connection, {
                'id': id, **body.model_dump(exclude={'email', 'password'}),
            })
    except Exception:
        try:
            admin_request('DELETE', f'/{id}')
        except Exception:
            logging.getLogger(__name__).error('Falha ao desfazer conta Auth após falha no perfil. Verificar contas sem perfil no painel.')
        raise
