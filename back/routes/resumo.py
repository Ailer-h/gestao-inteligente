from fastapi import APIRouter, Depends
from psycopg import Connection

from database import get_connection
from repositories import resumo as repository
from schemas.resumo import ResumoRead


router = APIRouter(prefix='/resumo', tags=['resumo'])


@router.get('', response_model=ResumoRead)
def consultar_resumo(connection: Connection = Depends(get_connection)):
    return repository.consultar(connection)
