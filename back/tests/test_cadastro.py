import sqlite3
import unittest
from unittest.mock import MagicMock, patch

import psycopg
from fastapi import HTTPException
from fastapi.testclient import TestClient

from database import get_connection
from main import app
from repositories import relatorio, vinculo
from schemas.cadastro import CadastroCreate
from schemas.crianca import CriancaCreate
from security import require_user
from services.cadastro import cadastrar


PESSOA = {'nome': 'Teste', 'sexo': 'F', 'rg': '123', 'cpf': '123', 'endereco': 'Rua'}
CRIANCA = {**PESSOA, 'frequenta_escola': True, 'nome_escola': 'Escola', 'serie_ano': 4}


class CadastroTest(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        app.dependency_overrides[get_connection] = lambda: self.connection
        app.dependency_overrides[require_user] = lambda: {'id': 'test'}
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()

    @patch('services.cadastro.vinculo.incluir')
    @patch('services.cadastro.crianca.incluir')
    @patch('services.cadastro.responsavel.incluir')
    def test_cadastro_cria_todas_as_relacoes_em_uma_transacao(self, criar_resp, criar_crianca, relacionar):
        criar_resp.side_effect = [{**PESSOA, 'id': 1}, {**PESSOA, 'id': 2}]
        criar_crianca.side_effect = [{**CRIANCA, 'id': 3}, {**CRIANCA, 'id': 4}]
        response = self.client.post('/cadastros', json={'responsaveis': [PESSOA, PESSOA], 'criancas': [CRIANCA, CRIANCA]})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.json()['criancas']), 2)
        self.assertEqual({call.args[1:] for call in relacionar.call_args_list}, {(3, 1), (3, 2), (4, 1), (4, 2)})
        self.connection.transaction.assert_called_once()

    @patch('services.cadastro.crianca.incluir', side_effect=psycopg.errors.UniqueViolation('duplicate'))
    @patch('services.cadastro.responsavel.incluir', return_value={**PESSOA, 'id': 1})
    def test_erro_na_crianca_sai_da_transacao_com_rollback(self, criar_resp, criar_crianca):
        body = CadastroCreate(responsaveis=[PESSOA], criancas=[CRIANCA])
        with self.assertRaises(psycopg.errors.UniqueViolation):
            cadastrar(self.connection, body)
        exit_args = self.connection.transaction.return_value.__exit__.call_args.args
        self.assertIs(exit_args[0], psycopg.errors.UniqueViolation)

    def test_responsavel_e_crianca_obrigatorios(self):
        for body in ({'responsaveis': [], 'criancas': [CRIANCA]}, {'responsaveis': [PESSOA], 'criancas': []}):
            self.assertEqual(self.client.post('/cadastros', json=body).status_code, 422)
        self.connection.execute.assert_not_called()

    def test_cadastro_sem_escola_limpa_dados(self):
        child = CriancaCreate(**{**CRIANCA, 'frequenta_escola': False})
        self.assertIsNone(child.nome_escola)
        self.assertIsNone(child.serie_ano)

    @patch('routes.crianca.repository.editar')
    @patch('routes.crianca.repository.consultar', return_value={**CRIANCA, 'id': 1})
    def test_edicao_sem_escola_limpa_dados_no_backend(self, consultar, editar):
        editar.return_value = {**CRIANCA, 'id': 1, 'frequenta_escola': False, 'nome_escola': None, 'serie_ano': None}
        response = self.client.patch('/criancas/1', json={'frequenta_escola': False})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(editar.call_args.args[2], {'frequenta_escola': False, 'nome_escola': None, 'serie_ano': None})

    @patch('routes.crianca.repository.editar')
    @patch('routes.crianca.repository.consultar', return_value={**CRIANCA, 'id': 1})
    @patch('routes.crianca.vinculo.substituir_responsaveis')
    def test_edicao_da_crianca_atualiza_responsaveis(self, alterar_vinculos, consultar, editar):
        response = self.client.patch('/criancas/1', json={'responsaveis_ids': [2, 3]})
        self.assertEqual(response.status_code, 200)
        alterar_vinculos.assert_called_once_with(self.connection, 1, [2, 3])
        editar.assert_not_called()

    @patch('routes.responsavel.repository.editar')
    @patch('routes.responsavel.repository.consultar', return_value={**PESSOA, 'id': 1})
    @patch('routes.responsavel.vinculo.substituir_criancas')
    def test_edicao_do_responsavel_atualiza_criancas(self, alterar_vinculos, consultar, editar):
        response = self.client.patch('/responsaveis/1', json={'criancas_ids': [4]})
        self.assertEqual(response.status_code, 200)
        alterar_vinculos.assert_called_once_with(self.connection, 1, [4])
        editar.assert_not_called()

    def test_crianca_nao_pode_receber_lista_vazia_ou_id_invalido(self):
        for ids in ([], [0], [-1]):
            self.assertEqual(self.client.patch('/criancas/1', json={'responsaveis_ids': ids}).status_code, 422)
        self.connection.execute.assert_not_called()

    @patch('repositories.vinculo.validar_ids')
    @patch('repositories.vinculo.criancas_do_responsavel', return_value=[{'id': 1}])
    def test_retirar_ultimo_responsavel_e_bloqueado_antes_de_excluir(self, consultar, validar):
        self.connection.execute.return_value.fetchall.side_effect = [[{'id': 1}], [{'id_crianca': 1}]]
        with self.assertRaises(HTTPException) as error:
            vinculo.substituir_criancas(self.connection, 2, [])
        self.assertEqual(error.exception.status_code, 409)
        self.assertFalse(any('DELETE' in str(call.args[0]) for call in self.connection.execute.call_args_list))

    def test_id_de_vinculo_inexistente_e_rejeitado(self):
        self.connection.execute.return_value.fetchall.return_value = [{'id': 1}]
        with self.assertRaises(HTTPException) as error:
            vinculo.validar_ids(self.connection, 'responsavel', [1, 999])
        self.assertEqual(error.exception.status_code, 422)

    @patch('routes.crianca.repository.excluir', return_value={'id': 1})
    def test_exclusao_da_crianca_remove_relacoes_na_mesma_transacao(self, excluir):
        response = self.client.delete('/criancas/1')
        self.assertEqual(response.status_code, 204)
        self.assertTrue(any('DELETE FROM public.relacao_responsavel_crianca' in str(call.args[0]) for call in self.connection.execute.call_args_list))
        self.connection.transaction.assert_called_once()

    @patch('routes.responsavel.repository.excluir')
    @patch('routes.responsavel.repository.consultar', return_value={**PESSOA, 'id': 1})
    @patch('routes.responsavel.vinculo.substituir_criancas', side_effect=HTTPException(status_code=409, detail='Último responsável.'))
    def test_exclusao_do_ultimo_responsavel_e_bloqueada(self, substituir, consultar, excluir):
        self.assertEqual(self.client.delete('/responsaveis/1').status_code, 409)
        excluir.assert_not_called()


class RankingTest(unittest.TestCase):
    def test_ranking_conta_criancas_distintas_somente_com_status_ativo(self):
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.row_factory = sqlite3.Row
        db.executescript('''
            ATTACH DATABASE ':memory:' AS public;
            CREATE TABLE public.atividade (id INTEGER PRIMARY KEY, nome TEXT);
            CREATE TABLE public.relacao_atividade_crianca (id_atividade INTEGER, id_crianca INTEGER, status INTEGER);
            INSERT INTO public.atividade VALUES (1, 'Pintura'), (2, 'Música'), (3, 'Sem inscritos');
            INSERT INTO public.relacao_atividade_crianca VALUES
                (1, 1, 1), (1, 1, 1), (1, 2, 0), (1, 3, 2), (2, 1, 1), (2, 2, 1);
        ''')
        class Adapter:
            def execute(self, query, params):
                return db.execute(query.replace('%s', '?'), params)
        rows = [dict(row) for row in relatorio.atividades_com_mais_criancas(Adapter(), 10)]
        self.assertEqual([(row['nome'], row['criancas_ativas']) for row in rows], [('Música', 2), ('Pintura', 1), ('Sem inscritos', 0)])
        self.assertEqual(len(relatorio.atividades_com_mais_criancas(Adapter(), 1)), 1)


if __name__ == '__main__':
    unittest.main()
