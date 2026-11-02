from pydantic import BaseModel


class ResumoRead(BaseModel):
    criancas: int
    responsaveis: int
    usuarios: int
    atividades: int
