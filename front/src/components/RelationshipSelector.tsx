import { useEffect, useState } from 'react'
import type { Dispatch, SetStateAction } from 'react'
import { apiRequest } from '../lib/api'
import type { RecordData } from '../lib/resources'

export interface RelationState { options: RecordData[]; selected: number[]; original: number[]; error?: string }

export default function RelationshipSelector({ resource, id, token, disabled, state, onChange }: {
  resource: 'criancas' | 'responsaveis'; id?: string | number; token: string; disabled: boolean
  state: RelationState | null; onChange: Dispatch<SetStateAction<RelationState | null>>
}) {
  const [search, setSearch] = useState('')
  const [attempt, setAttempt] = useState(0)
  const other = resource === 'criancas' ? 'responsaveis' : 'criancas'
  const label = resource === 'criancas' ? 'Responsáveis vinculados' : 'Crianças vinculadas'
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      const selected = id === undefined ? [] : await apiRequest<RecordData[]>(`/${resource}/${id}/${other}`, { signal: controller.signal }, token)
      const options: RecordData[] = []
      for (let offset = 0; ; offset += 100) {
        const page = await apiRequest<RecordData[]>(`/${other}?limit=100&offset=${offset}`, { signal: controller.signal }, token)
        options.push(...page)
        if (page.length < 100) break
      }
      if (!controller.signal.aborted) {
        const ids = selected.map(item => Number(item.id))
        onChange({ options, selected: ids, original: ids })
      }
    }
    load().catch(cause => { if (!controller.signal.aborted) onChange({ options: [], selected: [], original: [], error: cause.message }) })
    return () => controller.abort()
  }, [resource, id, other, token, onChange, attempt])
  return <fieldset className="relationship-selector" disabled={disabled}>
    <legend>{label}{resource === 'criancas' ? ' *' : ''}</legend>
    {!state ? <p role="status">Carregando vínculos…</p> : state.error ? <div className="feedback error" role="alert"><p>{state.error}</p><button type="button" className="secondary-button" onClick={() => { onChange(null); setAttempt(value => value + 1) }}>Tentar novamente</button></div> : <>
      <p>{state.selected.length} selecionado(s). {resource === 'criancas' ? 'Mantenha ao menos um responsável.' : 'Uma criança precisa manter ao menos um responsável.'}</p>
      <label>Buscar por nome ou CPF<input type="search" value={search} onChange={event => setSearch(event.target.value)} /></label>
      <div className="relationship-options">{state.options.filter(item => `${item.nome} ${item.cpf}`.toLocaleLowerCase('pt-BR').includes(search.toLocaleLowerCase('pt-BR'))).map(item => <label key={item.id} className="relationship-option">
        <input type="checkbox" checked={state.selected.includes(Number(item.id))} onChange={event => onChange(previous => previous ? {
          ...previous, selected: event.target.checked ? [...previous.selected, Number(item.id)] : previous.selected.filter(value => value !== Number(item.id)),
        } : previous)} />
        <span>{String(item.nome)}<small>CPF: {String(item.cpf)}</small></span>
      </label>)}</div>
      {!state.options.length && <p>Nenhum cadastro disponível para vincular.</p>}
    </>}
  </fieldset>
}
