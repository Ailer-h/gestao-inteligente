import assert from 'node:assert/strict'
import { afterEach, beforeEach, test } from 'node:test'
import { apiRequest, login, readSession, saveSession, SESSION_EXPIRED } from '../src/lib/api.ts'

const originalFetch = globalThis.fetch
let store
beforeEach(() => {
  store = new Map()
  globalThis.sessionStorage = {
    getItem: key => store.get(key) ?? null,
    setItem: (key, value) => store.set(key, value),
    removeItem: key => store.delete(key),
  }
  globalThis.window = new EventTarget()
})
afterEach(() => { globalThis.fetch = originalFetch })

test('login envia username e senha intacta e guarda somente a sessão de acesso', async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(url, 'http://127.0.0.1:8000/auth/login')
    assert.equal(options.method, 'POST')
    assert.deepEqual(JSON.parse(options.body), { username: 'admin', password: ' senha ' })
    assert.equal(options.headers.get('Authorization'), null)
    return Response.json({ access_token: 'token', expires_in: 3600, refresh_token: 'nao-guardar' })
  }
  const session = await login(' admin ', ' senha ')
  assert.equal(session.accessToken, 'token')
  assert.deepEqual(readSession(), session)
  assert.ok(!JSON.stringify([...store.values()]).includes('senha'))
  assert.ok(!JSON.stringify([...store.values()]).includes('nao-guardar'))
})

test('requisição protegida envia Bearer e aceita DELETE 204 sem JSON', async () => {
  globalThis.fetch = async (url, options) => {
    assert.ok(url.endsWith('/atividades/1'))
    assert.equal(options.headers.get('Authorization'), 'Bearer token')
    assert.equal(options.method, 'DELETE')
    return new Response(null, { status: 204 })
  }
  assert.equal(await apiRequest('/atividades/1', { method: 'DELETE' }, 'token'), undefined)
})

test('401 em rota protegida limpa a sessão e comunica expiração', async () => {
  saveSession({ accessToken: 'token', username: 'admin', expiresAt: Date.now() + 60000 })
  let expired = false
  window.addEventListener(SESSION_EXPIRED, () => { expired = true })
  globalThis.fetch = async () => Response.json({ detail: 'Token inválido ou expirado.' }, { status: 401 })
  await assert.rejects(apiRequest('/criancas', {}, 'token'), error => error.status === 401)
  assert.equal(readSession(), null)
  assert.ok(expired)
})

test('senha errada não dispara evento de expiração', async () => {
  let expired = false
  window.addEventListener(SESSION_EXPIRED, () => { expired = true })
  globalThis.fetch = async () => Response.json({ detail: 'Username ou senha inválidos.' }, { status: 401 })
  await assert.rejects(login('admin', 'errada'), /Username ou senha inválidos/)
  assert.equal(expired, false)
})

test('422 preserva a mensagem de validação e 409 preserva o conflito', async () => {
  globalThis.fetch = async () => Response.json({ detail: [{ loc: ['body', 'cpf'], msg: 'Campo obrigatório' }] }, { status: 422 })
  await assert.rejects(apiRequest('/usuarios'), /cpf: Campo obrigatório/)
  globalThis.fetch = async () => Response.json({ detail: 'Dados duplicados.' }, { status: 409 })
  await assert.rejects(apiRequest('/usuarios'), /Dados duplicados/)
})

test('falha de rede recebe mensagem legível', async () => {
  globalThis.fetch = async () => { throw new TypeError('fetch failed') }
  await assert.rejects(apiRequest('/health'), /Não foi possível conectar à API/)
})

test('sessão expirada ou corrompida não restaura o dashboard', () => {
  saveSession({ accessToken: 'token', username: 'admin', expiresAt: Date.now() - 1 })
  assert.equal(readSession(), null)
  store.set('girassol-session', '{invalid-json')
  assert.equal(readSession(), null)
})
