from fastapi import APIRouter, Depends, HTTPException, Query, Response
from psycopg import Connection

from database import get_connection
from repositories import crianca as repository
from repositories import vinculo
from repositories import inscricao
from schemas.inscricao import InscricaoRead
from schemas.crianca import CriancaCadastro, CriancaRead, CriancaUpdate
from schemas.responsavel import ResponsavelRead


router = APIRouter(prefix='/criancas', tags=['criancas'])


@router.get('/{id}/atividades', response_model=list[InscricaoRead])
def listar_atividades(id: int, connection: Connection = Depends(get_connection)):
    if repository.consultar(connection, id) is None:
        raise HTTPException(status_code=404, detail='Registro não encontrado.')
    return inscricao.listar(connection, 'crianca', id)


@router.get('/{id}/responsaveis', response_model=list[ResponsavelRead])
def listar_responsaveis(id: int, connection: Connection = Depends(get_connection)):
    if repository.consultar(connection, id) is None:
        raise HTTPException(status_code=404, detail='Registro não encontrado.')
    return vinculo.responsaveis_da_crianca(connection, id)


@router.get('', response_model=list[CriancaRead])
def listar(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    connection: Connection = Depends(get_connection),
):
    return repository.listar(connection, limit, offset)


@router.get('/{id}', response_model=CriancaRead)
def consultar(id: int, connection: Connection = Depends(get_connection)):
    record = repository.consultar(connection, id)
    if record is None:
        raise HTTPException(status_code=404, detail='Registro não encontrado.')
    return record


@router.post('', response_model=CriancaRead, status_code=201)
def incluir(body: CriancaCadastro, connection: Connection = Depends(get_connection)):
    with connection.transaction():
        record = repository.incluir(connection, body.model_dump(exclude={'atividades'}))
        if body.atividades:
            inscricao.substituir(connection, 'crianca', record['id'], [item.model_dump() for item in body.atividades])
        return record


@router.patch('/{id}', response_model=CriancaRead)
def editar(id: int, body: CriancaUpdate, connection: Connection = Depends(get_connection)):
    data = body.model_dump(include=body.model_fields_set)
    if not data:
        raise HTTPException(status_code=422, detail='Informe ao menos um campo para editar.')
    with connection.transaction():
        responsaveis_ids = data.pop('responsaveis_ids', None)
        atividades = data.pop('atividades', None)
        vinculo.bloquear_crianca(connection, id)
        record = repository.consultar(connection, id)
        if record is None:
            raise HTTPException(status_code=404, detail='Registro não encontrado.')
        if not data.get('frequenta_escola', record['frequenta_escola']):
            data.update(nome_escola=None, serie_ano=None)
        if data:
            record = repository.editar(connection, id, data)
        if responsaveis_ids is not None:
            vinculo.substituir_responsaveis(connection, id, responsaveis_ids)
        if atividades is not None:
            inscricao.substituir(connection, 'crianca', id, atividades)
        return record


@router.delete('/{id}', status_code=204, response_class=Response)
def excluir(id: int, connection: Connection = Depends(get_connection)):
    with connection.transaction():
        vinculo.bloquear_crianca(connection, id)
        vinculo.remover_da_crianca(connection, id)
        record = repository.excluir(connection, id)
        if record is None:
            raise HTTPException(status_code=404, detail='Registro não encontrado.')
    return Response(status_code=204)
