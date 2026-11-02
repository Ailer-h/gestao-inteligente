import { useEffect, useState } from 'react'
import type { Dispatch, SetStateAction } from 'react'
import { apiRequest } from '../lib/api'
import type { RecordData } from '../lib/resources'
import type { EnrollmentState } from '../lib/enrollments'

export default function EnrollmentSelector({ resource, id, token, state, onChange, disabled }: {
  resource: 'criancas' | 'atividades'; id?: string | number; token: string; disabled: boolean
  state: EnrollmentState | null; onChange: Dispatch<SetStateAction<EnrollmentState | null>>
}) {
  const other = resource === 'criancas' ? 'atividades' : 'criancas'
  const [search, setSearch] = useState('')
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      const current = id === undefined ? [] : await apiRequest<RecordData[]>(`/${resource}/${id}/${other}`, { signal: controller.signal }, token)
      const options: RecordData[] = []
      for (let offset = 0; ; offset += 100) {
        const page = await apiRequest<RecordData[]>(`/${other}?limit=100&offset=${offset}`, { signal: controller.signal }, token)
        options.push(...page)
        if (page.length < 100) break
      }
      const selected = current.map(item => ({ id: Number(item.id), status: Number(item.status ?? 2), data_entrada: String(item.data_entrada ?? new Date().toLocaleDateString('en-CA')) }))
      if (!controller.signal.aborted) onChange({ options, selected, original: selected })
    }
    load().catch(cause => { if (!controller.signal.aborted) onChange({ options: [], selected: [], original: [], error: cause.message }) })
    return () => controller.abort()
  }, [resource, other, id, token, onChange, attempt])
  return <fieldset className="relationship-selector" disabled={disabled}>
    <legend>{resource === 'criancas' ? 'Atividades vinculadas' : 'Crianças vinculadas'}</legend>
    {!state ? <p role="status">Carregando inscrições…</p> : state.error ? <div role="alert" className="feedback error"><p>{state.error}</p><button type="button" className="secondary-button" onClick={() => { onChange(null); setAttempt(value => value + 1) }}>Tentar novamente</button></div> : <>
      <p>Selecione os vínculos e informe o status. Novas inscrições começam como aguardando.</p>
      <label>Buscar por nome<input type="search" value={search} onChange={event => setSearch(event.target.value)} /></label>
      <div className="relationship-options">{state.options.filter(item => String(item.nome).toLocaleLowerCase('pt-BR').includes(search.toLocaleLowerCase('pt-BR'))).map(item => {
        const selected = state.selected.find(value => value.id === Number(item.id))
        return <div key={item.id} className="enrollment-row"><label className="relationship-option"><input type="checkbox" checked={!!selected} onChange={event => onChange(previous => previous ? { ...previous, selected: event.target.checked ? [...previous.selected, previous.original.find(value => value.id === Number(item.id)) ?? { id: Number(item.id), status: 2, data_entrada: new Date().toLocaleDateString('en-CA') }] : previous.selected.filter(value => value.id !== Number(item.id)) } : previous)} /><span>{String(item.nome)}</span></label>
          {selected && <div className="editor-grid"><div><label htmlFor={`enrollment-${resource}-${item.id}-status`}>Status de {String(item.nome)}</label><select id={`enrollment-${resource}-${item.id}-status`} value={selected.status} onChange={event => { const status = Number(event.target.value); onChange(previous => previous ? { ...previous, selected: previous.selected.map(value => value.id === selected.id ? { ...value, status } : value) } : previous) }}><option value="2">Aguardando</option><option value="1">Ativo</option><option value="0">Inativo</option></select></div>
          <div><label htmlFor={`enrollment-${resource}-${item.id}-date`}>Data de entrada de {String(item.nome)}</label><input id={`enrollment-${resource}-${item.id}-date`} type="date" required value={selected.data_entrada} onChange={event => { const data_entrada = event.target.value; onChange(previous => previous ? { ...previous, selected: previous.selected.map(value => value.id === selected.id ? { ...value, data_entrada } : value) } : previous) }} /></div></div>}
        </div>
      })}</div>
      {!state.options.length && <p>Nenhum cadastro disponível para vincular.</p>}
    </>}
  </fieldset>
}
