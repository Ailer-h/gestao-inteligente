import os
import sqlite3
import unittest
from unittest.mock import MagicMock, patch
from uuid import UUID

import psycopg
from fastapi.testclient import TestClient

from database import get_connection
from main import app
from repositories import usuario, inscricao
from security import require_user


ID = '12345678-1234-1234-1234-123456789abc'
PERFIL = {'id': ID, 'username': 'normal', 'cpf': '123', 'celular': None, 'cargo': 3}
BODY = {'username': 'normal', 'email': 'normal@example.com', 'password': ' senha ', 'cpf': '123'}


class UsuarioInscricaoTest(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        self.connection.execute.return_value.fetchone.return_value = None
        app.dependency_overrides[get_connection] = lambda: self.connection
        app.dependency_overrides[require_user] = lambda: {'id': ID}
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()

    @patch('services.usuario.repository.incluir', return_value=PERFIL)
    @patch('services.usuario.admin_request', return_value=UUID(ID))
    def test_usuario_autenticado_cria_conta_sem_uuid_e_sem_expor_senha(self, admin, incluir):
        response = self.client.post('/usuarios', json=BODY)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), PERFIL)
        self.assertEqual(admin.call_args.args[2], {'email': BODY['email'], 'password': ' senha ', 'email_confirm': True})
        self.assertEqual(incluir.call_args.args[1]['id'], UUID(ID))
        self.assertNotIn('password', incluir.call_args.args[1])
        self.assertNotIn('email', incluir.call_args.args[1])
        self.assertEqual(incluir.call_args.args[1]['cargo'], 3)

    @patch('services.usuario.repository.incluir', side_effect=psycopg.errors.UniqueViolation('duplicate'))
    @patch('services.usuario.admin_request', return_value=UUID(ID))
    def test_falha_no_perfil_desfaz_conta_externa(self, admin, incluir):
        # A conexão está simulada; o tradutor de IntegrityError da dependência real
        # não está ativo neste teste de compensação.
        with self.assertRaises(psycopg.errors.UniqueViolation):
            self.client.post('/usuarios', json=BODY)
        self.assertEqual(admin.call_args_list[-1].args, ('DELETE', f'/{ID}'))

    @patch('services.usuario.admin_request')
    def test_duplicidade_local_nao_cria_conta_externa(self, admin):
        self.connection.execute.return_value.fetchone.return_value = {'id': ID}
        self.assertEqual(self.client.post('/usuarios', json=BODY).status_code, 409)
        admin.assert_not_called()

    @patch('services.usuario.admin_request')
    def test_uuid_manual_cargo_zero_e_senha_curta_sao_recusados(self, admin):
        for body in ({**BODY, 'id': ID}, {**BODY, 'cargo': 0}, {**BODY, 'password': '123'}, {**BODY, 'email': 'invalido'}):
            self.assertEqual(self.client.post('/usuarios', json=body).status_code, 422)
        self.assertEqual(self.client.patch(f'/usuarios/{ID}', json={'cargo': 0}).status_code, 422)
        admin.assert_not_called()

    @patch('services.usuario.httpx.request')
    def test_chave_admin_ausente_falha_sem_acessar_supabase(self, request):
        with patch.dict(os.environ, {'SUPABASE_SERVICE_ROLE_KEY': ''}):
            self.assertEqual(self.client.post('/usuarios', json=BODY).status_code, 503)
        request.assert_not_called()

    @patch('routes.atividade.inscricao.substituir')
    @patch('routes.atividade.repository.consultar', return_value={'id': 1, 'nome': 'Pintura', 'tipo_atividade': 3})
    def test_edita_criancas_da_atividade_preservando_status_e_data(self, consultar, substituir):
        body = {'criancas': [{'id': 2, 'status': 1, 'data_entrada': '2026-11-02'}]}
        self.assertEqual(self.client.patch('/atividades/1', json=body).status_code, 200)
        self.assertEqual(substituir.call_args.args[1:3], ('atividade', 1))
        self.assertEqual(substituir.call_args.args[3][0]['status'], 1)
        self.assertEqual(str(substituir.call_args.args[3][0]['data_entrada']), '2026-11-02')

    @patch('routes.crianca.inscricao.substituir')
    @patch('routes.crianca.repository.consultar', return_value={'id': 1, 'nome': 'Ana', 'sexo': 'F', 'rg': '123', 'cpf': '123', 'endereco': 'Rua', 'frequenta_escola': True})
    def test_edita_atividades_da_crianca_com_padrao_aguardando(self, consultar, substituir):
        self.assertEqual(self.client.patch('/criancas/1', json={'atividades': [{'id': 3}]}).status_code, 200)
        self.assertEqual(substituir.call_args.args[1:3], ('crianca', 1))
        self.assertEqual(substituir.call_args.args[3][0]['status'], 2)

    @patch('routes.atividade.inscricao.substituir')
    @patch('routes.atividade.repository.incluir', return_value={'id': 1, 'nome': 'Pintura', 'tipo_atividade': 3})
    def test_cria_atividade_com_criancas(self, incluir, substituir):
        self.assertEqual(self.client.post('/atividades', json={'nome': 'Pintura', 'criancas': [{'id': 2}]}).status_code, 201)
        self.assertNotIn('criancas', incluir.call_args.args[1])
        self.assertEqual(substituir.call_args.args[3][0]['status'], 2)

    def test_ids_repetidos_sao_rejeitados_antes_de_escrever(self):
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as error:
            inscricao.substituir(self.connection, 'atividade', 1, [{'id': 2}, {'id': 2}])
        self.assertEqual(error.exception.status_code, 422)
        self.connection.execute.assert_not_called()

    def test_status_invalido_e_recusado(self):
        self.assertEqual(self.client.patch('/atividades/1', json={'criancas': [{'id': 2, 'status': 4}]}).status_code, 422)


class UsuariosOcultosTest(unittest.TestCase):
    def test_dev_nao_aparece_e_nao_pode_ser_editado_ou_excluido_pelas_rotas(self):
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.row_factory = sqlite3.Row
        db.executescript('''
            ATTACH DATABASE ':memory:' AS public;
            CREATE TABLE public.perfil_usuario (id TEXT PRIMARY KEY, username TEXT, cpf TEXT, cargo INT);
            INSERT INTO public.perfil_usuario VALUES ('dev', 'oculto', '0', 0), ('normal', 'visivel', '1', 3);
        ''')
        class Adapter:
            def execute(self, query, params):
                return db.execute(query.as_string().replace('%s', '?'), params)
        adapter = Adapter()
        self.assertEqual([row['id'] for row in usuario.listar(adapter, 1, 0)], ['normal'])
        self.assertIsNone(usuario.consultar(adapter, 'dev'))
        self.assertIsNone(usuario.editar(adapter, 'dev', {'username': 'alterado'}))
        self.assertIsNone(usuario.excluir(adapter, 'dev'))
        self.assertEqual(db.execute("SELECT username FROM public.perfil_usuario WHERE id = 'dev'").fetchone()[0], 'oculto')


if __name__ == '__main__':
    unittest.main()
