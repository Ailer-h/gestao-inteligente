from fastapi import HTTPException
from psycopg import Connection, sql

from repositories.vinculo import validar_ids


# Os identificadores SQL são escolhidos apenas a partir deste mapa interno.
CONFIG = {
    'atividade': ('id_atividade', 'id_crianca', 'crianca'),
    'crianca': ('id_crianca', 'id_atividade', 'atividade'),
}


def listar(connection: Connection, recurso: str, id: int):
    origem, destino, tabela = CONFIG[recurso]
    return connection.execute(sql.SQL(
        'SELECT p.id, p.nome, v.status, v.data_entrada FROM public.{} p '
        'JOIN public.relacao_atividade_crianca v ON v.{} = p.id '
        'WHERE v.{} = %s ORDER BY p.nome, p.id'
    ).format(sql.Identifier(tabela), sql.Identifier(destino), sql.Identifier(origem)), (id,)).fetchall()


def substituir(connection: Connection, recurso: str, id: int, itens: list[dict]):
    origem, destino, tabela = CONFIG[recurso]
    ids = [item['id'] for item in itens]
    if len(set(ids)) != len(ids):
        raise HTTPException(status_code=422, detail='Não repita a mesma criança ou atividade na lista.')
    # Bloqueia ambos os lados em ordem estável durante a substituição.
    connection.execute(sql.SQL('SELECT id FROM public.{} WHERE id = %s FOR UPDATE').format(
        sql.Identifier(recurso)), (id,))
    validar_ids(connection, tabela, ids)
    connection.execute(sql.SQL(
        'DELETE FROM public.relacao_atividade_crianca WHERE {} = %s AND NOT ({} = ANY(%s))'
    ).format(sql.Identifier(origem), sql.Identifier(destino)), (id, ids))
    for item in itens:
        connection.execute(sql.SQL(
            'INSERT INTO public.relacao_atividade_crianca ({}, {}, status, data_entrada) '
            'VALUES (%s, %s, %s, %s) ON CONFLICT (id_atividade, id_crianca) '
            'DO UPDATE SET status = EXCLUDED.status, data_entrada = EXCLUDED.data_entrada'
        ).format(sql.Identifier(origem), sql.Identifier(destino)),
            (id, item['id'], item['status'], item['data_entrada']))
