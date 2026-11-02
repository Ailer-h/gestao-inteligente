from fastapi import APIRouter, Depends
from psycopg import Connection

from database import get_connection
from schemas.cadastro import CadastroCreate, CadastroRead
from services.cadastro import cadastrar


router = APIRouter(prefix='/cadastros', tags=['cadastros'])


@router.post('', response_model=CadastroRead, status_code=201)
def incluir(body: CadastroCreate, connection: Connection = Depends(get_connection)):
    return cadastrar(connection, body)
