# Testes da API no Insomnia

## 1. Iniciar a API

No terminal, a partir da raiz do projeto:

```powershell
cd back
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

O `.env` da raiz precisa ter `DATABASE_URL`, `SUPABASE_URL` e `SUPABASE_ANON_KEY` preenchidos. As tabelas do projeto precisam existir no banco. O login usa a chave anon (ou a chave publishable equivalente), sem precisar da service role.

- URL base: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

No Insomnia, crie uma coleção HTTP. Nas requisições POST e PATCH, selecione **Body → JSON**. Use `Content-Type: application/json`. GET e DELETE não precisam de body.

As rotas de dados e `/health` exigem autenticação Bearer. O login e a documentação são públicos. Os testes escrevem no banco configurado no `.env`; use os dados fictícios abaixo em um ambiente de desenvolvimento.

## 2. Login e token

Para o primeiro login, use uma conta já existente com perfil e username. Depois de entrar, o próprio sistema cadastra novas contas automaticamente conforme a seção 7. O login continua recebendo username e password.

No Insomnia, configure esta requisição com **Auth → No Auth**, mesmo que a coleção tenha autenticação herdada:

```http
POST http://127.0.0.1:8000/auth/login
```

```json
{
  "username": "admin",
  "password": "sua-senha-de-teste"
}
```

Esperado: **200 OK**, com uma resposta neste formato (valores ilustrativos):

```json
{
  "access_token": "TOKEN_RETORNADO_PELO_SUPABASE",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "REFRESH_TOKEN_RETORNADO_PELO_SUPABASE",
  "user": {
    "id": "ID_USUARIO",
    "email": "seu-email-de-teste@example.com"
  }
}
```

Copie o **access_token**. Em cada requisição dos próximos passos, selecione **Auth → Bearer Token** e cole o token, sem escrever `Bearer` no campo. O Insomnia enviará:

```http
Authorization: Bearer SEU_ACCESS_TOKEN
```

Você também pode configurar Bearer Token na coleção/pasta e usar a autenticação herdada nas requisições protegidas. Mantenha o login com No Auth. Não use a anon key, a service role ou o refresh_token como token de acesso.

O prazo real do token vem em `expires_in`. Quando expirar, faça login novamente e substitua o access_token; esta API ainda não possui rota de renovação. Para testar pelo Swagger, faça login e use o botão **Authorize** com o access_token.

Antes de seguir, confira:

| Teste | Resultado esperado |
| --- | --- |
| Login com username inexistente ou senha errada | 401, com a mesma mensagem genérica |
| Login enviando email em vez de username | 422 |
| GET `/health` sem Authorization | 401 |
| GET `/health` com Bearer inválido ou expirado | 401 |
| GET `/health` com access_token válido | 200 |
| Rotas protegidas com Supabase Auth indisponível | 503, sem executar a operação |

## 3. Health

```http
GET http://127.0.0.1:8000/health
```

Esperado: **200 OK**.

```json
{"status": "ok"}
```

Esse endpoint confirma que a API está no ar. A conexão com o banco será exercitada nas próximas requisições.

## 4. Atividades

### Incluir

```http
POST http://127.0.0.1:8000/atividades
```

```json
{
  "nome": "Oficina de desenho - teste Insomnia",
  "data": "2026-11-10",
  "tipo_atividade": 3,
  "dia_atividade": null
}
```

Esperado: **201 Created**, com o registro e o `id` gerado. Anote esse ID e use no lugar de `ID_ATIVIDADE` abaixo.

Tipos: `1` Semanal, `2` Mensal, `3` Única. Se omitir `tipo_atividade`, o padrão é `3`. `dia_atividade` é um inteiro opcional; a API ainda não valida seu significado conforme a recorrência.

### Listar e consultar

```http
GET http://127.0.0.1:8000/atividades?limit=50&offset=0
GET http://127.0.0.1:8000/atividades/ID_ATIVIDADE
```

Crie uma requisição para cada URL. Esperado: **200 OK**, respectivamente uma lista e um objeto.

### Editar

```http
PATCH http://127.0.0.1:8000/atividades/ID_ATIVIDADE
```

```json
{
  "nome": "Oficina de pintura - teste Insomnia",
  "tipo_atividade": 2,
  "dia_atividade": 10
}
```

Esperado: **200 OK**, com os campos alterados. A `data` deve continuar igual, pois não foi enviada. Confirme com o GET individual.

## 5. Responsáveis

### Incluir

```http
POST http://127.0.0.1:8000/responsaveis
```

```json
{
  "nome": "Maria Teste Insomnia",
  "sexo": "F",
  "rg": "12.345.678-9",
  "cpf": "111.111.111-11",
  "celular": "(11) 99999-1111",
  "endereco": "Rua de Teste, 100"
}
```

Esperado: **201 Created**. Anote o `id` como `ID_RESPONSAVEL`.

### Listar e consultar

```http
GET http://127.0.0.1:8000/responsaveis
GET http://127.0.0.1:8000/responsaveis/ID_RESPONSAVEL
```

Esperado: **200 OK**.

### Editar

```http
PATCH http://127.0.0.1:8000/responsaveis/ID_RESPONSAVEL
```

```json
{
  "celular": "(11) 98888-2222",
  "endereco": "Rua de Teste, 200"
}
```

Esperado: **200 OK**. Nome, CPF e demais campos omitidos devem permanecer iguais.

## 6. Crianças

### Incluir

```http
POST http://127.0.0.1:8000/criancas
```

```json
{
  "nome": "Ana Teste Insomnia",
  "sexo": "F",
  "rg": "98.765.432-1",
  "cpf": "222.222.222-22",
  "celular": null,
  "endereco": "Rua de Teste, 100",
  "frequenta_escola": true,
  "nome_escola": "Escola de Teste",
  "serie_ano": 4,
  "necessidade_especial": null
}
```

Esperado: **201 Created**. Anote o `id` como `ID_CRIANCA`.

### Listar e consultar

```http
GET http://127.0.0.1:8000/criancas
GET http://127.0.0.1:8000/criancas/ID_CRIANCA
```

Esperado: **200 OK**.

### Editar

```http
PATCH http://127.0.0.1:8000/criancas/ID_CRIANCA
```

```json
{
  "serie_ano": 5,
  "necessidade_especial": "Descrição de teste"
}
```

Esperado: **200 OK**. Confirme os valores pelo GET.

Para limpar um campo opcional, envie um novo PATCH:

```json
{
  "necessidade_especial": null
}
```

Esperado: **200 OK**, com `necessidade_especial` igual a `null`.

## 7. Usuários (cadastro automático)

Com o token de qualquer usuário autenticado, envie:

```http
POST http://127.0.0.1:8000/usuarios
```

```json
{
  "username": "teste.insomnia",
  "email": "teste.insomnia@example.com",
  "password": "senha-de-teste-123",
  "cpf": "333.333.333-33",
  "celular": "(11) 97777-3333",
  "cargo": 3
}
```

Esperado: **201**, com ID gerado, username, CPF, celular e cargo. A resposta não inclui senha. Não envie UUID: a conta de acesso e o perfil são criados automaticamente. Use email e CPF ainda não cadastrados. A senha precisa ter pelo menos 6 caracteres e atender à política configurada no serviço. O backend precisa de `SUPABASE_SERVICE_ROLE_KEY` no `.env`; essa chave nunca vai para o frontend.

Copie o `id` retornado e use como `ID_USUARIO`:

```http
GET http://127.0.0.1:8000/usuarios
GET http://127.0.0.1:8000/usuarios/ID_USUARIO
```

Esperado: **200**. Usuários com cargo 0 são excluídos da listagem e da contagem; a consulta direta retorna **404**. Cargo 0 não aparece como opção no formulário e não é aceito no POST/PATCH (**422**). Cargos permitidos: 1 SuperADM, 2 ADM, 3 Atendente (padrão).

```http
PATCH http://127.0.0.1:8000/usuarios/ID_USUARIO
```

```json
{"username": "teste.insomnia.editado", "celular": null}
```

Esperado: **200**. Teste o login da conta criada usando seu username atual e a senha cadastrada. Email e senha são definidos na inclusão; não são editados por este PATCH. Excluir o perfil ainda mantém a conta de acesso.

## 8. Casos de erro

Execute antes da limpeza, usando os IDs de teste criados.

| Teste | Requisição / body | Esperado |
| --- | --- | --- |
| Tipo de atividade inválido | POST `/atividades` com `{"nome":"Teste","tipo_atividade":4}` | 422 |
| Nome obrigatório ausente | POST `/atividades` com `{}` | 422 |
| Nome vazio | PATCH `/atividades/ID_ATIVIDADE` com `{"nome":"   "}` | 422 |
| Null em campo obrigatório | PATCH `/atividades/ID_ATIVIDADE` com `{"nome":null}` | 422 |
| Edição sem campos | PATCH `/atividades/ID_ATIVIDADE` com `{}` | 422 |
| Campo desconhecido | PATCH `/atividades/ID_ATIVIDADE` com `{"campo_inexistente":1}` | 422 |
| Sexo inválido | PATCH `/criancas/ID_CRIANCA` com `{"sexo":"X"}` | 422 |
| UUID inválido | GET `/usuarios/abc` | 422 |
| Paginação inválida | GET `/atividades?limit=0` | 422 |
| CPF duplicado | Repetir o POST do responsável com o mesmo CPF | 409 |

Os erros retornam JSON com a chave `detail`. O **409** depende das constraints do banco conforme o SQL do projeto. Uma conexão indisponível retorna **503**.

Os CPFs acima são fictícios. A API atual valida tamanho e obrigatoriedade, mas ainda não valida dígitos verificadores ou aplica máscaras.

## 9. Excluir os registros de teste

Use somente os IDs que você anotou para estes testes. Cada requisição abaixo deve retornar **204 No Content**, sem body:

```http
DELETE http://127.0.0.1:8000/atividades/ID_ATIVIDADE
DELETE http://127.0.0.1:8000/criancas/ID_CRIANCA
DELETE http://127.0.0.1:8000/responsaveis/ID_RESPONSAVEL
DELETE http://127.0.0.1:8000/usuarios/ID_USUARIO
```

Crie uma requisição para cada URL. Depois, repita o GET individual: deve retornar **404 Not Found**. Repetir o DELETE do registro excluído também deve retornar **404**.

Se um registro tiver vínculos nas tabelas de relação, sua exclusão pode retornar **409**. Os passos de cadastro individual acima não criam vínculos; o cadastro geral da seção 11 cria.

O DELETE de `/usuarios` remove apenas o perfil. A conta de teste continua no Supabase Auth e pode ser removida pelo painel.

## 10. Conferência antes de integrar o frontend

- [ ] Login por username e senha retorna access_token com credenciais válidas.
- [ ] Rotas protegidas rejeitam token ausente, inválido ou expirado com 401.
- [ ] Health retorna 200 com token válido.
- [ ] Os quatro recursos incluem, listam, consultam e editam corretamente.
- [ ] PATCH preserva os campos omitidos e limpa os opcionais quando recebe null.
- [ ] Os padrões de tipo de atividade e cargo são 3.
- [ ] Casos inválidos retornam 422 e duplicidade retorna 409.
- [ ] Exclusão retorna 204; consulta após exclusão retorna 404.

O frontend já está integrado. O CORS permite `http://localhost:5173` e `http://127.0.0.1:5173`; outras origens podem ser configuradas por `CORS_ORIGINS` no `.env` da raiz. O token é validado no Supabase a cada requisição protegida. A autorização por cargo ainda não foi implementada: todo usuário autenticado pode acessar os quatro recursos.

O painel usa também `GET http://127.0.0.1:8000/resumo`, com o mesmo Bearer Token. A resposta traz os totais `criancas`, `responsaveis`, `usuarios` e `atividades`.

## 11. Cadastro geral e vínculos automáticos

No frontend, o botão “Formulário de cadastro” abre o painel lateral. O envio corresponde a:

```http
POST http://127.0.0.1:8000/cadastros
Authorization: Bearer SEU_ACCESS_TOKEN
```

```json
{
  "responsaveis": [
    {
      "nome": "Responsável do cadastro geral",
      "sexo": "F",
      "rg": "123456",
      "cpf": "444.444.444-44",
      "celular": null,
      "endereco": "Rua de Teste, 100"
    }
  ],
  "criancas": [
    {
      "nome": "Criança do cadastro geral",
      "sexo": "M",
      "rg": "654321",
      "cpf": "555.555.555-55",
      "celular": null,
      "endereco": "Rua de Teste, 100",
      "frequenta_escola": false,
      "nome_escola": null,
      "serie_ano": null,
      "necessidade_especial": null
    }
  ]
}
```

Esperado: **201**, com arrays `responsaveis` e `criancas`, incluindo os IDs gerados. Cada lista aceita de 1 a 20 pessoas. Dois responsáveis e duas crianças criam quatro vínculos. Use CPFs diferentes para cada pessoa e de outros registros existentes.

Consulte os vínculos:

```http
GET http://127.0.0.1:8000/criancas/ID_CRIANCA/responsaveis
GET http://127.0.0.1:8000/responsaveis/ID_RESPONSAVEL/criancas
```

Esperado: **200**, com os registros vinculados. Listas vazias no cadastro geral retornam **422**. Um CPF duplicado retorna **409** e desfaz todas as inclusões e vínculos desse envio.

## 12. Editar relações e escola

Para substituir os responsáveis de uma criança:

```http
PATCH http://127.0.0.1:8000/criancas/ID_CRIANCA
```

```json
{"responsaveis_ids": [1, 2]}
```

Para substituir as crianças de um responsável:

```http
PATCH http://127.0.0.1:8000/responsaveis/ID_RESPONSAVEL
```

```json
{"criancas_ids": [3, 4]}
```

Substitua os números pelos IDs reais. Esses arrays podem ser enviados junto aos campos normais, como `nome` e `celular`. Omitir o array mantém os vínculos. Enviar `criancas_ids: []` tenta remover todos os vínculos do responsável; retorna **409** se alguma criança ficar sem outro responsável. Enviar `responsaveis_ids: []` retorna **422**. IDs inexistentes retornam **422**.

Teste também um PATCH na criança com:

```json
{"frequenta_escola": false, "nome_escola": "Dado antigo", "serie_ano": 4}
```

Esperado: **200**, com `nome_escola` e `serie_ano` iguais a `null`. No frontend, esses campos ficam desabilitados ao selecionar “Não”.

Para limpar o cadastro geral de teste, exclua primeiro as crianças e depois os responsáveis. As relações são removidas automaticamente na exclusão da criança. Vínculos com atividades podem impedir a exclusão com **409**. Um responsável não pode ser excluído enquanto for o único responsável de alguma criança.

## 13. Relatório de atividades

```http
GET http://127.0.0.1:8000/relatorios/atividades?limit=10
```

Esperado: **200**, com uma lista de objetos `id`, `nome` e `criancas_ativas`, ordenada do maior para o menor número de crianças. Apenas `status = 1` em `relacao_atividade_crianca` entra na contagem; status 0 e 2 não entram. Atividades sem crianças ativas aparecem com zero. Sem atividades, a resposta é `[]`.

Os relatórios de renda foram cancelados.

## 14. Inscrições entre atividades e crianças

Consultar os vínculos, com Bearer Token:

```http
GET http://127.0.0.1:8000/criancas/ID_CRIANCA/atividades
GET http://127.0.0.1:8000/atividades/ID_ATIVIDADE/criancas
```

Cada item da resposta contém id, nome, status e data_entrada.

Para substituir as atividades de uma criança:

```http
PATCH http://127.0.0.1:8000/criancas/ID_CRIANCA
```

```json
{"atividades": [{"id": 1, "status": 1, "data_entrada": "2026-11-02"}]}
```

Para substituir as crianças de uma atividade:

```http
PATCH http://127.0.0.1:8000/atividades/ID_ATIVIDADE
```

```json
{"criancas": [{"id": 2, "status": 2, "data_entrada": "2026-11-02"}]}
```

Use IDs existentes. Os arrays substituem a lista completa: manter itens preserva seus vínculos, remover itens desfaz vínculos e enviar [] remove todos. Omitir o array não altera as inscrições. Status: 0 inativo, 1 ativo, 2 aguardando. Se omitidos em um item, status usa 2 e data_entrada usa a data atual. No frontend, a edição carrega e preserva status e datas existentes. IDs inexistentes, itens repetidos e status inválidos retornam 422. As alterações são transacionais.

Na inclusão de atividade, o POST aceita o mesmo campo criancas junto com nome, data e tipo_atividade. Depois de marcar uma inscrição como ativa, confira o aumento na contagem do relatório de atividades.
