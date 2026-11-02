from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Cadastro(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Pessoa(Cadastro):
    nome: str = Field(min_length=1, max_length=150)
    sexo: Literal['M', 'F']
    rg: str = Field(min_length=1, max_length=20)
    cpf: str = Field(min_length=1, max_length=14)
    celular: str | None = Field(default=None, max_length=20)
    endereco: str = Field(min_length=1, max_length=255)


class Atualizacao(Cadastro):
    campos_nao_nulos: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode='before')
    @classmethod
    def validar_campos_nao_nulos(cls, data):
        if isinstance(data, dict):
            for campo in cls.campos_nao_nulos:
                if campo in data and data[campo] is None:
                    raise ValueError(f'O campo {campo} não aceita null.')
        return data
