export type Resource = 'criancas' | 'responsaveis' | 'usuarios' | 'atividades'
export type RecordData = Record<string, string | number | boolean | null> & { id: string | number }
export interface Field {
  name: string
  label: string
  type?: 'text' | 'number' | 'date' | 'select' | 'email' | 'password'
  required?: boolean
  minLength?: number
  maxLength?: number
  createOnly?: boolean
  default?: string
  options?: [string, string][]
}
const person: Field[] = [
  { name: 'nome', label: 'Nome', required: true, maxLength: 150 },
  { name: 'sexo', label: 'Sexo', type: 'select', required: true, options: [['M', 'Masculino'], ['F', 'Feminino']] },
  { name: 'rg', label: 'RG', required: true, maxLength: 20 },
  { name: 'cpf', label: 'CPF', required: true, maxLength: 14 },
  { name: 'celular', label: 'Celular', maxLength: 20 },
  { name: 'endereco', label: 'Endereço', required: true, maxLength: 255 },
]
export const resources: Record<Resource, { label: string; fields: Field[]; columns: string[] }> = {
  criancas: { label: 'Alunos', columns: ['nome', 'cpf', 'nome_escola', 'serie_ano'], fields: [
    ...person,
    { name: 'frequenta_escola', label: 'Frequenta escola?', type: 'select', required: true, default: 'false', options: [['true', 'Sim'], ['false', 'Não']] },
    { name: 'nome_escola', label: 'Nome da escola', maxLength: 150 },
    { name: 'serie_ano', label: 'Série / ano', type: 'number' },
    { name: 'necessidade_especial', label: 'Necessidade especial', maxLength: 255 },
  ] },
  responsaveis: { label: 'Pais/Responsáveis', fields: person, columns: ['nome', 'cpf', 'celular', 'endereco'] },
  usuarios: { label: 'Usuários', columns: ['username', 'cpf', 'celular', 'cargo'], fields: [
    { name: 'username', label: 'Usuário', required: true, maxLength: 50 },
    { name: 'email', label: 'Email', type: 'email', required: true, maxLength: 254, createOnly: true },
    { name: 'password', label: 'Senha', type: 'password', required: true, minLength: 6, maxLength: 4096, createOnly: true },
    { name: 'cpf', label: 'CPF', required: true, maxLength: 14 },
    { name: 'celular', label: 'Celular', maxLength: 20 },
    { name: 'cargo', label: 'Cargo', type: 'select', required: true, default: '3', options: [['1', 'SuperADM'], ['2', 'ADM'], ['3', 'Atendente']] },
  ] },
  atividades: { label: 'Atividades', columns: ['nome', 'data', 'tipo_atividade', 'dia_atividade'], fields: [
    { name: 'nome', label: 'Nome', required: true, maxLength: 150 },
    { name: 'data', label: 'Data', type: 'date' },
    { name: 'tipo_atividade', label: 'Tipo de atividade', type: 'select', required: true, default: '3', options: [['1', 'Semanal'], ['2', 'Mensal'], ['3', 'Única']] },
    { name: 'dia_atividade', label: 'Dia da atividade', type: 'number' },
  ] },
}

export function toPayload(resource: Resource, values: Record<string, string>, original?: RecordData) {
  const payload: Record<string, string | number | boolean | null> = {}
  for (const field of resources[resource].fields) {
    if (original && field.createOnly) continue
    const raw = field.type === 'password' ? (values[field.name] ?? '') : (values[field.name] ?? '').trim()
    let value: string | number | boolean | null = raw || null
    if (raw && (field.type === 'number' || ['cargo', 'tipo_atividade'].includes(field.name))) value = Number(raw)
    if (field.name === 'frequenta_escola') value = raw === 'true'
    if (resource === 'criancas' && values.frequenta_escola === 'false' && ['nome_escola', 'serie_ano'].includes(field.name)) value = null
    if (!original || value !== (original[field.name] ?? null)) payload[field.name] = value
  }
  return payload
}

export function initialValues(resource: Resource) {
  return Object.fromEntries(resources[resource].fields.map(field => [field.name, field.default ?? '']))
}

export function displayValue(resource: Resource, name: string, value: RecordData[string]) {
  if (value === null || value === undefined || value === '') return '—'
  const field = resources[resource].fields.find(item => item.name === name)
  const option = field?.options?.find(([key]) => key === String(value))
  return option?.[1] ?? String(value)
}
