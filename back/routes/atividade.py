from fastapi import APIRouter, Depends, HTTPException, Query, Response
from psycopg import Connection

from database import get_connection
from repositories import atividade as repository
from repositories import inscricao
from schemas.inscricao import InscricaoRead
from schemas.atividade import AtividadeCreate, AtividadeRead, AtividadeUpdate


router = APIRouter(prefix='/atividades', tags=['atividades'])


@router.get('/{id}/criancas', response_model=list[InscricaoRead])
def listar_criancas(id: int, connection: Connection = Depends(get_connection)):
    if repository.consultar(connection, id) is None:
        raise HTTPException(status_code=404, detail='Registro não encontrado.')
    return inscricao.listar(connection, 'atividade', id)


@router.get('', response_model=list[AtividadeRead])
def listar(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    connection: Connection = Depends(get_connection),
):
    return repository.listar(connection, limit, offset)


@router.get('/{id}', response_model=AtividadeRead)
def consultar(id: int, connection: Connection = Depends(get_connection)):
    record = repository.consultar(connection, id)
    if record is None:
        raise HTTPException(status_code=404, detail='Registro não encontrado.')
    return record


@router.post('', response_model=AtividadeRead, status_code=201)
def incluir(body: AtividadeCreate, connection: Connection = Depends(get_connection)):
    with connection.transaction():
        data = body.model_dump()
        criancas = data.pop('criancas')
        record = repository.incluir(connection, data)
        if criancas:
            inscricao.substituir(connection, 'atividade', record['id'], criancas)
        return record


@router.patch('/{id}', response_model=AtividadeRead)
def editar(id: int, body: AtividadeUpdate, connection: Connection = Depends(get_connection)):
    data = body.model_dump(include=body.model_fields_set)
    if not data:
        raise HTTPException(status_code=422, detail='Informe ao menos um campo para editar.')
    with connection.transaction():
        criancas = data.pop('criancas', None)
        record = repository.consultar(connection, id)
        if record is None:
            raise HTTPException(status_code=404, detail='Registro não encontrado.')
        if data:
            record = repository.editar(connection, id, data)
        if criancas is not None:
            inscricao.substituir(connection, 'atividade', id, criancas)
        return record


@router.delete('/{id}', status_code=204, response_class=Response)
def excluir(id: int, connection: Connection = Depends(get_connection)):
    record = repository.excluir(connection, id)
    if record is None:
        raise HTTPException(status_code=404, detail='Registro não encontrado.')
    return Response(status_code=204)
