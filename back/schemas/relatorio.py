from pydantic import BaseModel


class AtividadeRankingRead(BaseModel):
    id: int
    nome: str
    criancas_ativas: int
