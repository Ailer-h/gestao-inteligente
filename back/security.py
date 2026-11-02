from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from schemas.auth import AuthUser
from services.auth import unauthorized, validate_token


bearer = HTTPBearer(auto_error=False)


def require_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> AuthUser:
    if credentials is None or credentials.scheme.lower() != 'bearer':
        raise unauthorized('Envie o token em Authorization: Bearer <token>.')
    return validate_token(credentials.credentials)
