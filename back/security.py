from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database import get_connection
from schemas.auth import AuthUser
from services.auth import unauthorized, validate_token


bearer = HTTPBearer(auto_error=False)


def require_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> AuthUser:
    if credentials is None or credentials.scheme.lower() != 'bearer':
        raise unauthorized('Envie o token em Authorization: Bearer <token>.')
    return validate_token(credentials.credentials)


def require_profile(user: AuthUser = Depends(require_user), connection = Depends(get_connection)):
    user_id = user['id'] if isinstance(user, dict) else user.id
    profile = connection.execute('SELECT * FROM public.perfil_usuario WHERE id = %s', (user_id,)).fetchone()
    if profile is None or profile['cargo'] not in (0, 1, 2, 3):
        raise HTTPException(status_code=403, detail='Perfil sem permissão de acesso.')
    return profile


def require_user_manager(profile = Depends(require_profile)):
    if profile['cargo'] not in (0, 1, 2):
        raise HTTPException(status_code=403, detail='Atendentes não têm acesso aos usuários.')
    return profile


def check_managed_role(profile, cargo):
    allowed = {0: (1, 2, 3), 1: (2, 3), 2: (3,)}
    if cargo not in allowed.get(profile['cargo'], ()):
        raise HTTPException(status_code=403, detail='Você não pode gerenciar usuários deste cargo.')
