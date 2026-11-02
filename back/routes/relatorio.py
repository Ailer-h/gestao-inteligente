from fastapi import APIRouter, Depends, Query
from psycopg import Connection

from database import get_connection
from repositories import relatorio as repository
from schemas.relatorio import AtividadeRankingRead


router = APIRouter(prefix='/relatorios', tags=['relatorios'])


@router.get('/atividades', response_model=list[AtividadeRankingRead])
def atividades_com_mais_criancas(
    limit: int = Query(default=10, ge=1, le=100),
    connection: Connection = Depends(get_connection),
):
    return repository.atividades_com_mais_criancas(connection, limit)
