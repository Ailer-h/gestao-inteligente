from pydantic import Field

from schemas.base import Cadastro
from schemas.crianca import CriancaCreate, CriancaRead
from schemas.responsavel import ResponsavelCreate, ResponsavelRead


class CadastroCreate(Cadastro):
    responsaveis: list[ResponsavelCreate] = Field(min_length=1, max_length=20)
    criancas: list[CriancaCreate] = Field(min_length=1, max_length=20)


class CadastroRead(Cadastro):
    responsaveis: list[ResponsavelRead]
    criancas: list[CriancaRead]
