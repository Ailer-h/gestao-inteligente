from fastapi import APIRouter, Depends, Response
from psycopg import Connection

from database import get_connection
from schemas.auth import LoginRequest, TokenResponse
from services.auth import login
from security import require_profile


router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/login', response_model=TokenResponse)
def autenticar(body: LoginRequest, response: Response, connection: Connection = Depends(get_connection)):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    return login(body, connection)


@router.get('/me')
def perfil(profile = Depends(require_profile)):
    return {'cargo': profile['cargo'], 'username': profile['username']}
