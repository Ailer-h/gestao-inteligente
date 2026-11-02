# Gestão Inteligente

- `front/`: React, TypeScript, Vite e configurações do frontend.
- `back/`: FastAPI, teste de conexão, requirements.txt e `.venv/`.
- Raiz: `.env`, `.env.example` e `.gitignore`.

Estrutura do backend:

```text
back/
├── main.py
├── database.py
├── config.py
├── security.py
├── routes/
│   ├── auth.py
│   ├── cadastro.py
│   ├── relatorio.py
│   ├── resumo.py
│   ├── atividade.py
│   ├── crianca.py
│   ├── responsavel.py
│   └── usuario.py
├── schemas/
│   ├── inscricao.py
│   ├── auth.py
│   ├── base.py
│   ├── cadastro.py
│   ├── relatorio.py
│   ├── resumo.py
│   ├── atividade.py
│   ├── crianca.py
│   ├── responsavel.py
│   └── usuario.py
├── repositories/
│   ├── inscricao.py
│   ├── relatorio.py
│   ├── resumo.py
│   ├── atividade.py
│   ├── crianca.py
│   ├── responsavel.py
│   ├── usuario.py
│   └── vinculo.py
├── services/
│   ├── auth.py
│   ├── cadastro.py
│   └── usuario.py
├── tests/
├── test_db.py
├── requirements.txt
└── .venv/
```

As rotas recebem as requisições HTTP, os schemas validam os dados e os repositories executam as consultas SQL. A conexão fica em `database.py`, compartilhada entre os recursos.

## Frontend

```powershell
cd front
npm install
npm run dev
```

Build de produção: `npm run build` dentro de `front/`.

O frontend usa `http://127.0.0.1:8000` como API por padrão. Para alterar, copie `front/.env.example` para `front/.env`, ajuste `VITE_API_URL` e reinicie o Vite. As credenciais do Supabase e do PostgreSQL permanecem apenas no `.env` da raiz.

O Vite roda na porta 5173 e avisa se ela estiver ocupada. O backend permite CORS para `http://localhost:5173` e `http://127.0.0.1:5173`. Para outra origem, configure `CORS_ORIGINS` no `.env` da raiz, separando as origens por vírgula, e reinicie a API.

## Integração frontend e backend

Mantenha os dois servidores rodando em terminais separados. Acesse `http://localhost:5173` e entre com o username do perfil e a senha da conta no Supabase Auth.

- O login envia username e senha para `/auth/login` e as requisições seguintes usam Bearer Token.
- A sessão de acesso fica no sessionStorage da aba; senha e refresh token não são armazenados. Sem storage disponível, a sessão funciona em memória.
- Ao expirar o token ou receber 401 numa rota protegida, a tela retorna ao login. Sair limpa a sessão local; não revoga o token no Supabase.
- Alunos, responsáveis, usuários e atividades oferecem listagem em cards/tabela, inclusão, edição parcial e exclusão com confirmação. As listas exibem páginas de até 50 registros.
- A tela inicial consulta os totais atuais em `GET /resumo`, protegido pelo token. O relatório de atividades compara as inscrições ativas atuais; não representa histórico.
- Qualquer usuário autenticado pode cadastrar outro usuário com username, email, senha, CPF, celular e cargo (1, 2 ou 3). O backend cria a conta de acesso e o perfil automaticamente, sem pedir UUID. A senha não é armazenada na tabela de perfil.
- O formulário geral abre em um painel lateral à direita, com ao menos um responsável e uma criança. É possível adicionar várias pessoas; todos os responsáveis informados são vinculados a todas as crianças do mesmo envio. O backend confirma tudo em uma transação, sem cadastros parciais em caso de erro.
- A edição de crianças permite selecionar seus responsáveis; a edição de responsáveis permite selecionar as crianças vinculadas. Uma criança precisa manter ao menos um responsável. Para vincular pessoas já cadastradas, use essas telas de edição.
- “Não frequenta escola” desabilita e limpa nome da escola e série/ano. O backend também limpa esses dados.
- A página inicial exibe o ranking de até 10 atividades com mais crianças, considerando somente inscrições ativas (`status = 1`). Os relatórios de renda foram cancelados e não há campos de renda.
- As fichas de crianças e atividades permitem selecionar inscrições, status (0 inativo, 1 ativo, 2 aguardando) e data de entrada. Novas inscrições começam como aguardando. O cadastro de atividade também permite incluir crianças.

Para conferir o fluxo, faça login, abra cada recurso, inclua um registro de teste, edite, recarregue a página para conferir a persistência e exclua o registro. Confira também uma senha incorreta e o botão Sair. As operações alteram o banco configurado no backend.

Testes do cliente HTTP e dos payloads do frontend (Node.js 24):

```powershell
cd front
npm test
npm run build
npm run lint
```

## Backend

Execute dentro de `back/`, com o ambiente virtual já criado:

```powershell
cd back
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

- Documentação: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## Autenticação

Preencha `SUPABASE_URL` e `SUPABASE_ANON_KEY` no `.env` da raiz. Use um usuário existente no Supabase Auth com email confirmado, quando essa confirmação estiver habilitada, e um perfil em `public.perfil_usuario` com o mesmo UUID e username único. O primeiro acesso precisa de uma conta com perfil já existente; após o login, as demais contas são criadas pelo próprio sistema. A conexão PostgreSQL precisa de permissão de leitura em `auth.users` para resolver o email internamente. O username diferencia maiúsculas e minúsculas.

1. Envie `POST /auth/login` com JSON `{"username":"admin", "password":"sua-senha"}`.
2. Copie `access_token` da resposta.
3. Envie `Authorization: Bearer <access_token>` nas rotas de dados e no `/health`.

Login e documentação (`/docs`, `/redoc`, `/openapi.json`) são públicos. No Swagger, use o botão **Authorize** para informar o token. Token ausente, inválido ou expirado retorna 401. A API não gera tokens próprios: o login retorna a sessão emitida pelo Supabase. Quando o token expirar, faça login novamente; ainda não há rota de renovação.

## Rotas

Roteiro manual de testes: [Testes no Insomnia](back/TESTES_INSOMNIA.md).

Os recursos `/atividades`, `/usuarios`, `/responsaveis` e `/criancas` oferecem:

| Método | Caminho | Operação |
| --- | --- | --- |
| GET | `/recurso` | Listar (limit de 1 a 100, padrão 50; offset padrão 0) |
| GET | `/recurso/{id}` | Consultar |
| POST | `/recurso` | Incluir |
| PATCH | `/recurso/{id}` | Editar somente os campos enviados |
| DELETE | `/recurso/{id}` | Excluir |

Endpoints adicionais, todos protegidos pelo mesmo Bearer Token:

| Método | Caminho | Operação |
| --- | --- | --- |
| POST | `/cadastros` | Cadastrar responsáveis e crianças e criar todos os vínculos |
| GET | `/criancas/{id}/responsaveis` | Consultar responsáveis vinculados |
| GET | `/responsaveis/{id}/criancas` | Consultar crianças vinculadas |
| GET | `/criancas/{id}/atividades` | Consultar inscrições da criança |
| GET | `/atividades/{id}/criancas` | Consultar inscrições da atividade |
| GET | `/relatorios/atividades?limit=10` | Ranking de inscrições ativas por atividade |

No PATCH de criança, `responsaveis_ids` substitui seus responsáveis (mínimo 1). No PATCH de responsável, `criancas_ids` substitui suas crianças; retirar o último responsável de uma criança retorna 409. Omitir esses campos preserva os vínculos. Alterações de dados e vínculos são confirmadas na mesma transação. Excluir uma criança remove seus vínculos com responsáveis; inscrições em atividades ainda podem impedir sua exclusão. Excluir um responsável também respeita a regra de não deixar crianças sem responsável.

`/usuarios` cria automaticamente a conta no Supabase Auth e seu perfil em `public.perfil_usuario`. O POST recebe username, email, password, CPF, celular e cargo; o ID é gerado pelo serviço. A criação usa `SUPABASE_SERVICE_ROLE_KEY` apenas no backend, conforme a [API administrativa do Supabase](https://supabase.com/docs/reference/python/auth-admin-createuser). O email é confirmado automaticamente. Se o perfil falhar, o backend tenta remover a conta recém-criada; falhas dessa compensação são registradas para revisão das contas sem perfil no painel. Excluir um perfil por esta API ainda mantém a conta de acesso. Usuários de cargo 0 não aparecem na listagem, consulta individual ou contagem e não podem ser alterados/excluídos por essas rotas; cargo 0 também não é aceito no cadastro ou edição.

As tabelas precisam existir conforme o schema do projeto. Conflitos de unicidade ou de chaves estrangeiras retornam 409; registros inexistentes retornam 404; dados inválidos retornam 422. As rotas de dados e `/health` exigem token Bearer validado no Supabase Auth a cada requisição. O controle de acesso por cargo ainda não foi implementado: qualquer usuário autenticado pode acessar os quatro recursos.

Para executar os testes das rotas com banco simulado, dentro de `back/`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Banco de dados

Para configurar um novo ambiente, copie `.env.example` para `.env` e preencha as credenciais. Preserve o `.env` existente.

Execute o teste dentro de `back/`:

```powershell
.\.venv\Scripts\python.exe test_db.py
```

No PATCH de criança, `atividades` é a lista completa de inscrições; no PATCH (ou POST) de atividade, use `criancas`. Cada item tem `id`, `status` (padrão 2) e `data_entrada` (padrão data atual). Omitir a lista preserva as inscrições existentes; enviar `[]` remove todos os vínculos desse lado. Os dados e as inscrições são gravados em uma transação.
