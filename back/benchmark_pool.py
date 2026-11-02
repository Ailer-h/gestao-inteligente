"""Read-only benchmark using the same pool configuration as the API."""
import asyncio
import json
from statistics import median
from time import perf_counter
from types import SimpleNamespace

from database import database_lifespan


async def main():
    app = SimpleNamespace(state=SimpleNamespace())
    start = perf_counter()
    async with database_lifespan(app):
        pool = app.state.database_pool
        if pool is None:
            raise RuntimeError('DATABASE_URL missing')
        startup_ms = (perf_counter() - start) * 1000
        await asyncio.to_thread(pool.wait, timeout=15)
        warmup_ms = (perf_counter() - start) * 1000
        acquisition, query, total = [], [], []
        for _ in range(7):
            start = perf_counter()
            with pool.connection() as conn:
                acquired = perf_counter()
                acquisition.append((acquired - start) * 1000)
                # Read-only transaction; no application data is returned or modified.
                conn.execute('SELECT 1').fetchone()
                query.append((perf_counter() - acquired) * 1000)
            total.append((perf_counter() - start) * 1000)
        print(json.dumps({
            'startup_nonblocking_ms': round(startup_ms, 2),
            'background_warmup_ms': round(warmup_ms, 2),
            'warm_acquisition_median_ms': round(median(acquisition), 3),
            'select1_median_ms': round(median(query), 2),
            'transaction_total_median_ms': round(median(total), 2),
        }, indent=2))


if __name__ == '__main__':
    asyncio.run(main())
