from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from psycopg import Connection

from database import get_connection
from repositories import usuario as repository
from schemas.usuario import UsuarioCreate, UsuarioRead, UsuarioUpdate
from services.usuario import cadastrar


router = APIRouter(prefix='/usuarios', tags=['usuarios'])


@router.get('', response_model=list[UsuarioRead])
def listar(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    connection: Connection = Depends(get_connection),
):
    return repository.listar(connection, limit, offset)


@router.get('/{id}', response_model=UsuarioRead)
def consultar(id: UUID, connection: Connection = Depends(get_connection)):
    record = repository.consultar(connection, id)
    if record is None:
        raise HTTPException(status_code=404, detail='Registro não encontrado.')
    return record


@router.post('', response_model=UsuarioRead, status_code=201)
def incluir(body: UsuarioCreate, connection: Connection = Depends(get_connection)):
    return cadastrar(connection, body)


@router.patch('/{id}', response_model=UsuarioRead)
def editar(id: UUID, body: UsuarioUpdate, connection: Connection = Depends(get_connection)):
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=422, detail='Informe ao menos um campo para editar.')
    record = repository.editar(connection, id, data)
    if record is None:
        raise HTTPException(status_code=404, detail='Registro não encontrado.')
    return record


@router.delete('/{id}', status_code=204, response_class=Response)
def excluir(id: UUID, connection: Connection = Depends(get_connection)):
    record = repository.excluir(connection, id)
    if record is None:
        raise HTTPException(status_code=404, detail='Registro não encontrado.')
    return Response(status_code=204)
