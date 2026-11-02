import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.atividade import router as atividade_router
from routes.crianca import router as crianca_router
from routes.responsavel import router as responsavel_router
from routes.usuario import router as usuario_router
from routes.auth import router as auth_router
from routes.resumo import router as resumo_router
from routes.cadastro import router as cadastro_router
from routes.relatorio import router as relatorio_router
from security import require_user


app = FastAPI(title='Gestão Inteligente')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv(
        'CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173'
    ).split(',') if origin.strip()],
    allow_methods=['GET', 'POST', 'PATCH', 'DELETE'],
    allow_headers=['Authorization', 'Content-Type'],
)

app.include_router(auth_router)

for router in (atividade_router, crianca_router, responsavel_router, usuario_router, resumo_router, cadastro_router, relatorio_router):
    app.include_router(router, dependencies=[Depends(require_user)])


@app.get('/health', tags=['Health'], dependencies=[Depends(require_user)])
def health() -> dict[str, str]:
    return {'status': 'ok'}
