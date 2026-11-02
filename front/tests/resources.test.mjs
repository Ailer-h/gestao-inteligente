import assert from 'node:assert/strict'
import { test } from 'node:test'
import { displayValue, resources, toPayload } from '../src/lib/resources.ts'
import { enrollmentPayload } from '../src/lib/enrollments.ts'

test('atividade converte inteiros, mantém padrão 3 e envia data opcional como null', () => {
  assert.deepEqual(toPayload('atividades', { nome: ' Oficina ', data: '', tipo_atividade: '3', dia_atividade: '0' }), {
    nome: 'Oficina', data: null, tipo_atividade: 3, dia_atividade: 0,
  })
})

test('criança que não frequenta escola limpa nome e série mesmo com dados antigos', () => {
  const payload = toPayload('criancas', { nome: 'Ana', frequenta_escola: 'false', nome_escola: 'Antiga', serie_ano: '4' })
  assert.equal(payload.frequenta_escola, false)
  assert.equal(payload.serie_ano, null)
  assert.equal(payload.nome_escola, null)
  assert.equal(payload.necessidade_especial, null)
})

test('criança que frequenta escola mantém o nome e converte a série', () => {
  const payload = toPayload('criancas', { nome: 'Ana', frequenta_escola: 'true', nome_escola: 'Escola', serie_ano: '4' })
  assert.equal(payload.frequenta_escola, true)
  assert.equal(payload.serie_ano, 4)
  assert.equal(payload.nome_escola, 'Escola')
})

test('edição envia somente campos alterados e permite limpar um opcional', () => {
  const original = { id: 1, nome: 'Oficina', data: '2026-11-02', tipo_atividade: 3, dia_atividade: null }
  assert.deepEqual(toPayload('atividades', { nome: 'Oficina', data: '', tipo_atividade: '3', dia_atividade: '' }, original), { data: null })
})

test('edição de usuário ignora dados de criação e altera cargo normal', () => {
  const original = { id: 'uuid', username: 'admin', cpf: '123', celular: null, cargo: 3 }
  assert.deepEqual(toPayload('usuarios', { id: 'outro', username: 'admin', cpf: '123', celular: '', cargo: '2', email: 'ignore@example.com', password: 'ignorar' }, original), { cargo: 2 })
})

test('rótulos refletem os enums do banco e valores opcionais', () => {
  assert.equal(displayValue('atividades', 'tipo_atividade', 3), 'Única')
  assert.equal(displayValue('usuarios', 'cargo', 2), 'ADM')
  assert.equal(displayValue('criancas', 'frequenta_escola', false), 'Não')
  assert.equal(displayValue('criancas', 'serie_ano', null), '—')
})

test('cadastro de usuário envia email e senha intacta sem UUID nem cargo Dev', () => {
  const payload = toPayload('usuarios', { username: ' normal ', email: ' teste@example.com ', password: ' senha ', cpf: '123', cargo: '3' })
  assert.equal(payload.password, ' senha ')
  assert.equal(payload.email, 'teste@example.com')
  assert.equal(payload.username, 'normal')
  assert.ok(!('id' in payload))
  assert.ok(!resources.usuarios.fields.find(field => field.name === 'cargo').options.some(([value]) => value === '0'))
})

test('inscrições não alteradas não enviam payload; status, data e remoções são enviados', () => {
  const item = { id: 1, status: 2, data_entrada: '2026-11-02' }
  const state = { options: [], selected: [item], original: [item] }
  assert.equal(enrollmentPayload(state), null)
  assert.deepEqual(enrollmentPayload({ ...state, selected: [{ ...item, status: 1 }] }), [{ ...item, status: 1 }])
  assert.deepEqual(enrollmentPayload({ ...state, selected: [] }), [])
})
