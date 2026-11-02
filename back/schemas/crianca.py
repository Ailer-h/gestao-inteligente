from typing import Literal

from pydantic import Field, PositiveInt, model_validator

from schemas.base import Pessoa, Atualizacao
from schemas.inscricao import Inscricao


class CriancaCreate(Pessoa):
    frequenta_escola: bool
    nome_escola: str | None = Field(default=None, max_length=150)
    serie_ano: int | None = None
    necessidade_especial: str | None = Field(default=None, max_length=255)

    @model_validator(mode='after')
    def limpar_escola(self):
        if not self.frequenta_escola:
            self.nome_escola = None
            self.serie_ano = None
        return self


class CriancaUpdate(Atualizacao):
    campos_nao_nulos = frozenset({'nome', 'sexo', 'rg', 'cpf', 'endereco', 'frequenta_escola'})

    nome: str | None = Field(default=None, min_length=1, max_length=150)
    sexo: Literal['M', 'F'] | None = None
    rg: str | None = Field(default=None, min_length=1, max_length=20)
    cpf: str | None = Field(default=None, min_length=1, max_length=14)
    celular: str | None = Field(default=None, max_length=20)
    endereco: str | None = Field(default=None, min_length=1, max_length=255)
    frequenta_escola: bool | None = None
    nome_escola: str | None = Field(default=None, max_length=150)
    serie_ano: int | None = None
    necessidade_especial: str | None = Field(default=None, max_length=255)
    responsaveis_ids: list[PositiveInt] = Field(default_factory=list, min_length=1, max_length=100)
    atividades: list[Inscricao] = Field(default_factory=list, max_length=100)


class CriancaRead(CriancaCreate):
    id: int


class CriancaCadastro(CriancaCreate):
    atividades: list[Inscricao] = Field(default_factory=list, max_length=100)
