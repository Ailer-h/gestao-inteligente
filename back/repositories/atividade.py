from psycopg import Connection, sql


def listar(connection: Connection, limit: int, offset: int):
    return connection.execute(
        sql.SQL('SELECT * FROM public.atividade ORDER BY id LIMIT %s OFFSET %s'),
        (limit, offset),
    ).fetchall()


def consultar(connection: Connection, id: int):
    return connection.execute(
        sql.SQL('SELECT * FROM public.atividade WHERE id = %s'), (id,)
    ).fetchone()


def incluir(connection: Connection, data: dict):
    return connection.execute(
        sql.SQL('INSERT INTO public.atividade ({}) VALUES ({}) RETURNING *').format(
            sql.SQL(', ').join(map(sql.Identifier, data)),
            sql.SQL(', ').join(sql.Placeholder() for _ in data),
        ),
        tuple(data.values()),
    ).fetchone()


def editar(connection: Connection, id: int, data: dict):
    return connection.execute(
        sql.SQL('UPDATE public.atividade SET {} WHERE id = %s RETURNING *').format(
            sql.SQL(', ').join(
                sql.SQL('{} = %s').format(sql.Identifier(field)) for field in data
            ),
        ),
        (*data.values(), id),
    ).fetchone()


def excluir(connection: Connection, id: int):
    return connection.execute(
        sql.SQL('DELETE FROM public.atividade WHERE id = %s RETURNING id'), (id,)
    ).fetchone()
