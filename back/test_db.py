import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    database_url = os.getenv('DATABASE_URL', '').strip()

    if not database_url:
        print('Preencha DATABASE_URL no .env antes de executar o teste.')
        return 1

    try:
        with psycopg.connect(
            database_url, connect_timeout=10, sslmode='require'
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
                if result != (1,):
                    print('O banco retornou um resultado inesperado.')
                    return 1
    except (psycopg.Error, ValueError):
        print(
            'Falha na conexão. Confira DATABASE_URL, usuário, senha, '
            'host, porta e acesso à rede. '
            'Se necessário, use a conexão do pooler do Supabase.'
        )
        return 1

    print('Conexão com o banco realizada com sucesso! SELECT 1 retornou 1.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
