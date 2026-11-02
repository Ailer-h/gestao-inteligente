from datetime import date
from typing import Literal

from pydantic import Field

from schemas.base import Cadastro, Atualizacao
from schemas.inscricao import Inscricao


class AtividadeBase(Cadastro):
    nome: str = Field(min_length=1, max_length=150)
    data: date | None = None
    tipo_atividade: Literal[1, 2, 3] = 3
    dia_atividade: int | None = None


class AtividadeCreate(AtividadeBase):
    criancas: list[Inscricao] = Field(default_factory=list, max_length=100)


class AtividadeUpdate(Atualizacao):
    campos_nao_nulos = frozenset({'nome', 'tipo_atividade'})

    nome: str | None = Field(default=None, min_length=1, max_length=150)
    data: date | None = None
    tipo_atividade: Literal[1, 2, 3] | None = None
    dia_atividade: int | None = None
    criancas: list[Inscricao] = Field(default_factory=list, max_length=100)


class AtividadeRead(AtividadeBase):
    id: int
    tipo_atividade: Literal[1, 2, 3]
