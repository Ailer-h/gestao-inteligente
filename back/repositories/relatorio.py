from psycopg import Connection


def atividades_com_mais_criancas(connection: Connection, limit: int):
    return connection.execute(
        'SELECT a.id, a.nome, COUNT(DISTINCT v.id_crianca) AS criancas_ativas '
        'FROM public.atividade a '
        'LEFT JOIN public.relacao_atividade_crianca v ON v.id_atividade = a.id AND v.status = 1 '
        'GROUP BY a.id, a.nome ORDER BY criancas_ativas DESC, a.nome, a.id LIMIT %s',
        (limit,),
    ).fetchall()
