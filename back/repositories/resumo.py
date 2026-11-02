from psycopg import Connection


def consultar(connection: Connection):
    return connection.execute(
        'SELECT '
        '(SELECT COUNT(*) FROM public.crianca) AS criancas, '
        '(SELECT COUNT(*) FROM public.responsavel) AS responsaveis, '
        '(SELECT COUNT(*) FROM public.perfil_usuario WHERE cargo IS DISTINCT FROM 0) AS usuarios, '
        '(SELECT COUNT(*) FROM public.atividade) AS atividades'
    ).fetchone()
