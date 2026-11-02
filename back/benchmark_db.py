"""Read-only database timing; never prints credentials or person records."""
import json
import os
from pathlib import Path
from statistics import median
from time import perf_counter

import psycopg
from dotenv import load_dotenv


def main():
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    url = os.environ['DATABASE_URL']
    connections = []
    for _ in range(3):
        start = perf_counter()
        with psycopg.connect(url, connect_timeout=10, sslmode='require', autocommit=True) as conn:
            connections.append((perf_counter() - start) * 1000)
    results = {'connection_ms': connections, 'queries': {}}
    with psycopg.connect(url, connect_timeout=10, sslmode='require', autocommit=True) as conn:
        conn.execute('SET default_transaction_read_only = on')
        conn.execute("SET statement_timeout = '5s'")
        queries = {'roundtrip': ('SELECT 1', ())}
        for table in ('crianca', 'responsavel', 'atividade'):
            queries[table] = (f'SELECT * FROM public.{table} ORDER BY id LIMIT %s OFFSET %s', (100, 0))
        child = conn.execute('SELECT id FROM public.crianca ORDER BY id LIMIT 1').fetchone()
        if child:
            queries['child_guardians'] = ('SELECT r.* FROM public.responsavel r JOIN public.relacao_responsavel_crianca v ON v.id_responsavel = r.id WHERE v.id_crianca = %s ORDER BY r.nome, r.id', child)
            queries['child_activities'] = ('SELECT p.id, p.nome, v.status, v.data_entrada FROM public.atividade p JOIN public.relacao_atividade_crianca v ON v.id_atividade = p.id WHERE v.id_crianca = %s ORDER BY p.nome, p.id', child)
        for name, (query, params) in queries.items():
            durations = []
            for _ in range(7):
                start = perf_counter()
                rows = conn.execute(query, params).fetchall()
                durations.append((perf_counter() - start) * 1000)
            plan = conn.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ' + query, params).fetchone()[0][0]
            results['queries'][name] = {'rows': len(rows), 'first_ms': round(durations[0], 2), 'median_ms': round(median(durations[1:]), 2), 'server_planning_ms': plan['Planning Time'], 'server_execution_ms': plan['Execution Time']}
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (psycopg.Error, KeyError, ValueError) as error:
        print(json.dumps({'error_type': type(error).__name__, 'message': 'Benchmark failed; check database connectivity/configuration.'}))
        raise SystemExit(1)
