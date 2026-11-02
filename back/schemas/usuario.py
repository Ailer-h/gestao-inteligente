from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field, SecretStr, field_validator

from schemas.base import Cadastro, Atualizacao


class UsuarioCreate(Cadastro):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=False)

    username: str = Field(min_length=1, max_length=50)
    email: str = Field(max_length=254, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    password: SecretStr = Field(min_length=6, max_length=4096)
    cpf: str = Field(min_length=1, max_length=14)
    celular: str | None = Field(default=None, max_length=20)
    cargo: Literal[1, 2, 3] = 3

    @field_validator('username', 'email', 'cpf', 'celular', mode='before')
    @classmethod
    def limpar_texto(cls, value):
        return value.strip() if isinstance(value, str) else value


class UsuarioUpdate(Atualizacao):
    campos_nao_nulos = frozenset({'username', 'cpf', 'cargo'})

    username: str | None = Field(default=None, min_length=1, max_length=50)
    cpf: str | None = Field(default=None, min_length=1, max_length=14)
    celular: str | None = Field(default=None, max_length=20)
    cargo: Literal[1, 2, 3] | None = None


class UsuarioRead(Cadastro):
    id: UUID
    username: str | None = None
    cpf: str
    celular: str | None = None
    cargo: Literal[0, 1, 2, 3] | None
