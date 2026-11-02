from psycopg import Connection

from repositories import crianca, responsavel, vinculo
from schemas.cadastro import CadastroCreate


def cadastrar(connection: Connection, body: CadastroCreate):
    # Qualquer erro desfaz pessoas e vínculos de todo o cadastro.
    with connection.transaction():
        responsaveis = [responsavel.incluir(connection, item.model_dump()) for item in body.responsaveis]
        criancas = [crianca.incluir(connection, item.model_dump()) for item in body.criancas]
        for aluno in criancas:
            for adulto in responsaveis:
                vinculo.incluir(connection, aluno['id'], adulto['id'])
        return {'responsaveis': responsaveis, 'criancas': criancas}
