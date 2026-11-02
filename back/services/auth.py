import os

import httpx
from fastapi import HTTPException
from pydantic import ValidationError
from psycopg import Connection
from uuid import UUID

import config
from schemas.auth import AuthUser, LoginRequest, TokenResponse
from repositories.usuario import consultar_login


def unauthorized(detail: str = 'Token inválido ou expirado.') -> HTTPException:
    return HTTPException(
        status_code=401, detail=detail, headers={'WWW-Authenticate': 'Bearer'}
    )


def auth_request(method: str, path: str, *, token: str | None = None, **kwargs) -> dict:
    url = os.getenv('SUPABASE_URL', '').strip().rstrip('/')
    key = os.getenv('SUPABASE_ANON_KEY', '').strip()
    if not url or not key:
        raise HTTPException(status_code=503, detail='Supabase Auth não configurado.')

    headers = {'apikey': key}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    try:
        response = httpx.request(
            method, f'{url}/auth/v1/{path}', headers=headers,
            timeout=10, follow_redirects=False, **kwargs,
        )
    except httpx.RequestError as error:
        raise HTTPException(status_code=503, detail='Serviço de autenticação indisponível.') from error

    if response.status_code in (400, 401, 403, 422):
        raise unauthorized('Token inválido ou expirado.' if token else 'Username ou senha inválidos, ou conta indisponível.')
    if response.status_code == 429:
        raise HTTPException(status_code=429, detail='Muitas tentativas. Aguarde antes de tentar novamente.')
    if not response.is_success:
        raise HTTPException(status_code=503, detail='Serviço de autenticação indisponível.')
    try:
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError('Resposta inesperada')
        return data
    except ValueError as error:
        raise HTTPException(status_code=502, detail='Resposta inválida do serviço de autenticação.') from error


def login(body: LoginRequest, connection: Connection) -> TokenResponse:
    account = consultar_login(connection, body.username)
    if not account or not account['email']:
        raise unauthorized('Username ou senha inválidos, ou conta indisponível.')
    data = auth_request(
        'POST', 'token', params={'grant_type': 'password'},
        json={'email': account['email'], 'password': body.password.get_secret_value()},
    )
    try:
        session = TokenResponse.model_validate(data)
    except ValidationError as error:
        raise HTTPException(status_code=502, detail='Resposta inválida do serviço de autenticação.') from error
    if session.user.id != UUID(str(account['id'])):
        raise unauthorized('Username ou senha inválidos, ou conta indisponível.')
    return session


def validate_token(token: str) -> AuthUser:
    # O servidor do Supabase verifica o token; decodificar o JWT sozinho não o valida.
    data = auth_request('GET', 'user', token=token)
    try:
        return AuthUser.model_validate(data)
    except ValidationError as error:
        raise unauthorized() from error
