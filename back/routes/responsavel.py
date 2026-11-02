from fastapi import APIRouter, Depends, HTTPException, Query, Response
from psycopg import Connection

from database import get_connection
from repositories import responsavel as repository
from repositories import vinculo
from schemas.crianca import CriancaRead
from schemas.responsavel import ResponsavelCreate, ResponsavelRead, ResponsavelUpdate


router = APIRouter(prefix='/responsaveis', tags=['responsaveis'])


@router.get('/{id}/criancas', response_model=list[CriancaRead])
def listar_criancas(id: int, connection: Connection = Depends(get_connection)):
    if repository.consultar(connection, id) is None:
        raise HTTPException(status_code=404, detail='Registro não encontrado.')
    return vinculo.criancas_do_responsavel(connection, id)


@router.get('', response_model=list[ResponsavelRead])
def listar(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    connection: Connection = Depends(get_connection),
):
    return repository.listar(connection, limit, offset)


@router.get('/{id}', response_model=ResponsavelRead)
def consultar(id: int, connection: Connection = Depends(get_connection)):
    record = repository.consultar(connection, id)
    if record is None:
        raise HTTPException(status_code=404, detail='Registro não encontrado.')
    return record


@router.post('', response_model=ResponsavelRead, status_code=201)
def incluir(body: ResponsavelCreate, connection: Connection = Depends(get_connection)):
    return repository.incluir(connection, body.model_dump())


@router.patch('/{id}', response_model=ResponsavelRead)
def editar(id: int, body: ResponsavelUpdate, connection: Connection = Depends(get_connection)):
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=422, detail='Informe ao menos um campo para editar.')
    with connection.transaction():
        criancas_ids = data.pop('criancas_ids', None)
        record = repository.consultar(connection, id)
        if record is None:
            raise HTTPException(status_code=404, detail='Registro não encontrado.')
        if data:
            record = repository.editar(connection, id, data)
        if criancas_ids is not None:
            vinculo.substituir_criancas(connection, id, criancas_ids)
        return record


@router.delete('/{id}', status_code=204, response_class=Response)
def excluir(id: int, connection: Connection = Depends(get_connection)):
    with connection.transaction():
        if repository.consultar(connection, id) is None:
            raise HTTPException(status_code=404, detail='Registro não encontrado.')
        vinculo.substituir_criancas(connection, id, [])
        record = repository.excluir(connection, id)
        if record is None:
            raise HTTPException(status_code=404, detail='Registro não encontrado.')
    return Response(status_code=204)
