from typing import Literal

from pydantic import Field, PositiveInt

from schemas.base import Pessoa, Atualizacao


class ResponsavelCreate(Pessoa):
    pass


class ResponsavelUpdate(Atualizacao):
    campos_nao_nulos = frozenset({'nome', 'sexo', 'rg', 'cpf', 'endereco'})

    nome: str | None = Field(default=None, min_length=1, max_length=150)
    sexo: Literal['M', 'F'] | None = None
    rg: str | None = Field(default=None, min_length=1, max_length=20)
    cpf: str | None = Field(default=None, min_length=1, max_length=14)
    celular: str | None = Field(default=None, max_length=20)
    endereco: str | None = Field(default=None, min_length=1, max_length=255)
    criancas_ids: list[PositiveInt] = Field(default_factory=list, max_length=100)


class ResponsavelRead(ResponsavelCreate):
    id: int


class ResponsavelCadastro(ResponsavelCreate):
    criancas_ids: list[PositiveInt] = Field(default_factory=list, max_length=100)
