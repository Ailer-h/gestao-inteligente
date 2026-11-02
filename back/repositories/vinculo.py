from fastapi import HTTPException
from psycopg import Connection, sql


def responsaveis_da_crianca(connection: Connection, id: int):
    return connection.execute(
        'SELECT r.* FROM public.responsavel r '
        'JOIN public.relacao_responsavel_crianca v ON v.id_responsavel = r.id '
        'WHERE v.id_crianca = %s ORDER BY r.nome, r.id', (id,),
    ).fetchall()


def criancas_do_responsavel(connection: Connection, id: int):
    return connection.execute(
        'SELECT c.* FROM public.crianca c '
        'JOIN public.relacao_responsavel_crianca v ON v.id_crianca = c.id '
        'WHERE v.id_responsavel = %s ORDER BY c.nome, c.id', (id,),
    ).fetchall()


def incluir(connection: Connection, crianca_id: int, responsavel_id: int):
    connection.execute(
        'INSERT INTO public.relacao_responsavel_crianca (id_crianca, id_responsavel) '
        'VALUES (%s, %s) ON CONFLICT (id_crianca, id_responsavel) DO NOTHING',
        (crianca_id, responsavel_id),
    )


def bloquear_crianca(connection: Connection, crianca_id: int):
    connection.execute('SELECT id FROM public.crianca WHERE id = %s FOR UPDATE', (crianca_id,))


def remover_da_crianca(connection: Connection, crianca_id: int):
    connection.execute(
        'DELETE FROM public.relacao_responsavel_crianca WHERE id_crianca = %s', (crianca_id,),
    )


def validar_ids(connection: Connection, table: str, ids: list[int]):
    ids = sorted(set(ids))
    if not ids:
        return
    rows = connection.execute(
        sql.SQL('SELECT id FROM public.{} WHERE id = ANY(%s) ORDER BY id FOR KEY SHARE').format(
            sql.Identifier(table)
        ), (ids,),
    ).fetchall()
    if {row['id'] for row in rows} != set(ids):
        raise HTTPException(status_code=422, detail='Um ou mais vínculos informados não existem.')


def substituir_responsaveis(connection: Connection, crianca_id: int, ids: list[int]):
    # Serializa as alterações de vínculos da mesma criança.
    bloquear_crianca(connection, crianca_id)
    validar_ids(connection, 'responsavel', ids)
    remover_da_crianca(connection, crianca_id)
    for responsavel_id in sorted(set(ids)):
        incluir(connection, crianca_id, responsavel_id)


def substituir_criancas(connection: Connection, responsavel_id: int, ids: list[int]):
    atuais = {row['id'] for row in criancas_do_responsavel(connection, responsavel_id)}
    desejados = set(ids)
    afetados = sorted(atuais | desejados)
    if afetados:
        connection.execute(
            'SELECT id FROM public.crianca WHERE id = ANY(%s) ORDER BY id FOR UPDATE', (afetados,),
        ).fetchall()
    validar_ids(connection, 'crianca', ids)
    removidos = sorted(atuais - desejados)
    if removidos:
        sem_outro = connection.execute(
            'SELECT id_crianca FROM public.relacao_responsavel_crianca '
            'WHERE id_crianca = ANY(%s) GROUP BY id_crianca HAVING COUNT(*) <= 1', (removidos,),
        ).fetchall()
        if sem_outro:
            raise HTTPException(status_code=409, detail='Uma criança não pode ficar sem responsável. Vincule outro responsável antes de remover este vínculo.')
        connection.execute(
            'DELETE FROM public.relacao_responsavel_crianca '
            'WHERE id_responsavel = %s AND id_crianca = ANY(%s)', (responsavel_id, removidos),
        )
    for crianca_id in sorted(desejados):
        incluir(connection, crianca_id, responsavel_id)
