from uuid import UUID

from psycopg import Connection, sql


def consultar_login(connection: Connection, username: str):
    return connection.execute(
        sql.SQL(
            'SELECT perfil.id, conta.email '
            'FROM public.perfil_usuario AS perfil '
            'JOIN auth.users AS conta ON conta.id = perfil.id '
            'WHERE perfil.username = %s'
        ),
        (username,),
    ).fetchone()


def listar(connection: Connection, limit: int, offset: int):
    return connection.execute(
        sql.SQL('SELECT * FROM public.perfil_usuario WHERE cargo IS DISTINCT FROM 0 ORDER BY id LIMIT %s OFFSET %s'),
        (limit, offset),
    ).fetchall()


def consultar(connection: Connection, id: UUID):
    return connection.execute(
        sql.SQL('SELECT * FROM public.perfil_usuario WHERE id = %s AND cargo IS DISTINCT FROM 0'), (id,)
    ).fetchone()


def incluir(connection: Connection, data: dict):
    return connection.execute(
        sql.SQL('INSERT INTO public.perfil_usuario ({}) VALUES ({}) RETURNING *').format(
            sql.SQL(', ').join(map(sql.Identifier, data)),
            sql.SQL(', ').join(sql.Placeholder() for _ in data),
        ),
        tuple(data.values()),
    ).fetchone()


def editar(connection: Connection, id: UUID, data: dict):
    return connection.execute(
        sql.SQL('UPDATE public.perfil_usuario SET {} WHERE id = %s AND cargo IS DISTINCT FROM 0 RETURNING *').format(
            sql.SQL(', ').join(
                sql.SQL('{} = %s').format(sql.Identifier(field)) for field in data
            ),
        ),
        (*data.values(), id),
    ).fetchone()


def excluir(connection: Connection, id: UUID):
    return connection.execute(
        sql.SQL('DELETE FROM public.perfil_usuario WHERE id = %s AND cargo IS DISTINCT FROM 0 RETURNING id'), (id,)
    ).fetchone()
