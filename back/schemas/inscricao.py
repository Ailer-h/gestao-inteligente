from datetime import date
from typing import Literal

from pydantic import Field, PositiveInt

from schemas.base import Cadastro


class Inscricao(Cadastro):
    id: PositiveInt
    status: Literal[0, 1, 2] = 2
    data_entrada: date = Field(default_factory=date.today)


class InscricaoRead(Inscricao):
    nome: str
    status: Literal[0, 1, 2] | None
    data_entrada: date | None
