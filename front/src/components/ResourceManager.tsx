import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { apiRequest } from '../lib/api'
import { displayValue, resources, toPayload } from '../lib/resources'
import type { RecordData, Resource } from '../lib/resources'
import Drawer from './Drawer'
import PersonFields from './PersonFields'
import FamilyRegistration from './FamilyRegistration'
import RelationshipSelector from './RelationshipSelector'
import type { RelationState } from './RelationshipSelector'
import EnrollmentSelector from './EnrollmentSelector'
import type { EnrollmentState } from '../lib/enrollments'
import { enrollmentPayload } from '../lib/enrollments'

const PAGE_SIZE = 50

export default function ResourceManager({ resource, token, view, onViewChange }: {
  resource: Resource; token: string; view: 'cards' | 'table'
  onViewChange: (view: 'cards' | 'table') => void
}) {
  const config = resources[resource]
  const [records, setRecords] = useState<RecordData[]>([])
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [editor, setEditor] = useState<{ record?: RecordData } | null>(null)
  const [deleting, setDeleting] = useState<RecordData | null>(null)
  const [saving, setSaving] = useState(false)
  const [refresh, setRefresh] = useState(0)
  const reload = useCallback(() => setRefresh(value => value + 1), [])

  useEffect(() => {
    const controller = new AbortController()
    apiRequest<RecordData[]>(`/${resource}?limit=${PAGE_SIZE}&offset=${offset}`, { signal: controller.signal }, token)
      .then(data => { if (!controller.signal.aborted) setRecords(resource === 'usuarios' ? data.filter(item => item.cargo !== 0) : data) })
      .catch(cause => { if (!controller.signal.aborted) setError(cause.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [resource, token, offset, refresh])

  function refreshList() { setLoading(true); setError(''); reload() }
  function changePage(nextOffset: number) { setLoading(true); setError(''); setOffset(nextOffset) }

  async function remove() {
    if (!deleting || saving) return
    setSaving(true); setError(''); setNotice('')
    try {
      await apiRequest(`/${resource}/${encodeURIComponent(deleting.id)}`, { method: 'DELETE' }, token)
      setDeleting(null)
      setNotice('Registro excluído com sucesso.')
      if (records.length === 1 && offset > 0) changePage(offset - PAGE_SIZE)
      else refreshList()
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Não foi possível excluir.') }
    finally { setSaving(false) }
  }

  return <section className="records-section" aria-label={`Listagem de ${config.label}`}>
    <div className="records-toolbar">
      <span className="records-count">{loading ? 'Carregando…' : `Página ${offset / PAGE_SIZE + 1} · ${records.length} registros`}</span>
      <div className="record-actions">
        <button className="secondary-button" onClick={refreshList} disabled={loading || saving}>Atualizar</button>
        <div className="view-switch" role="group" aria-label="Modo de visualização">{(['cards', 'table'] as const).map(mode => <button key={mode} onClick={() => onViewChange(mode)} aria-pressed={view === mode} className={view === mode ? 'selected' : ''}>{mode === 'cards' ? 'Cards' : 'Tabela'}</button>)}</div>
        <button className="primary-button" onClick={() => { setEditor({}); setNotice(''); setError('') }}>Novo cadastro</button>
      </div>
    </div>
    {notice && <p className="feedback success" role="status">{notice}</p>}
    {error && <p className="feedback error" role="alert">{error}</p>}
    {editor && !editor.record && (resource === 'criancas' || resource === 'responsaveis') ? <FamilyRegistration token={token} onClose={() => setEditor(null)} onSaved={() => { setEditor(null); setNotice('Cadastro e vínculos salvos com sucesso.'); refreshList() }} /> : editor && <RecordEditor key={editor.record?.id ?? 'new'} resource={resource} token={token} record={editor.record}
      onCancel={() => setEditor(null)} onSaved={() => { setEditor(null); setNotice('Cadastro salvo com sucesso.'); refreshList() }} />}
    {deleting && <div className="delete-confirm feedback" role="alert">
      <p>Excluir “{String(deleting.nome ?? deleting.username ?? deleting.id)}”? Esta ação não pode ser desfeita.{resource === 'usuarios' ? ' A conta de acesso será mantida.' : ''}</p>
      <div className="record-actions"><button className="danger-button" disabled={saving} onClick={remove}>{saving ? 'Excluindo…' : 'Confirmar exclusão'}</button><button className="secondary-button" disabled={saving} onClick={() => setDeleting(null)}>Cancelar</button></div>
    </div>}
    {loading ? <p className="records-empty" role="status">Carregando cadastros…</p> : error ? <button className="secondary-button" onClick={refreshList}>Tentar carregar novamente</button> : !records.length ? <div className="records-empty records-card-empty"><h2>Nenhum cadastro nesta página</h2><p>Use “Novo cadastro” para começar.</p></div> : view === 'table' ? <div className="records-table-wrap"><table className="records-table">
      <caption className="sr-only">{config.label}</caption><thead><tr>{config.columns.map(name => <th key={name}>{config.fields.find(field => field.name === name)?.label}</th>)}<th>Ações</th></tr></thead>
      <tbody>{records.map(record => <tr key={record.id}>{config.columns.map(name => <td key={name}>{displayValue(resource, name, record[name])}</td>)}<td>{actions(record)}</td></tr>)}</tbody>
    </table></div> : <div className="record-grid">{records.map(record => <article className="record-card" key={record.id}>
      <h2>{String(record.nome ?? record.username ?? 'Usuário sem nome')}</h2><dl>{config.columns.map(name => <div key={name}><dt>{config.fields.find(field => field.name === name)?.label}</dt><dd>{displayValue(resource, name, record[name])}</dd></div>)}</dl>{actions(record)}
    </article>)}</div>}
    <div className="pagination"><button className="secondary-button" disabled={offset === 0 || loading || saving} onClick={() => changePage(offset - PAGE_SIZE)}>Anterior</button><span>Página {offset / PAGE_SIZE + 1}</span><button className="secondary-button" disabled={records.length < PAGE_SIZE || loading || saving || !!error} onClick={() => changePage(offset + PAGE_SIZE)}>Próxima</button></div>
  </section>

  function actions(record: RecordData) {
    return <div className="record-actions"><button className="secondary-button" disabled={saving} onClick={() => { setEditor({ record }); setError(''); setNotice('') }}>Editar</button><button className="danger-button" disabled={saving} onClick={() => { setDeleting(record); setError(''); setNotice('') }}>Excluir</button></div>
  }
}

function RecordEditor({ resource, token, record, onCancel, onSaved }: {
  resource: Resource; token: string; record?: RecordData; onCancel: () => void; onSaved: () => void
}) {
  const fields = resources[resource].fields.filter(field => !record || !field.createOnly)
  const [values, setValues] = useState<Record<string, string>>(() => Object.fromEntries(fields.map(field => [field.name,
    record ? String(record[field.name] ?? '') : field.default ?? '',
  ])))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [relations, setRelations] = useState<RelationState | null>(null)
  const [enrollments, setEnrollments] = useState<EnrollmentState | null>(null)
  const hasEnrollments = resource === 'atividades' || (!!record && resource === 'criancas')
  const hasRelations = !!record && (resource === 'criancas' || resource === 'responsaveis')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving) return
    const payload = toPayload(resource, values, record)
    if (hasRelations) {
      if (!relations || relations.error) { setError('Carregue os vínculos antes de salvar.'); return }
      if (resource === 'criancas' && !relations.selected.length) { setError('Selecione ao menos um responsável.'); return }
      const sorted = (ids: number[]) => [...ids].sort((a, b) => a - b).join(',')
      if (sorted(relations.selected) !== sorted(relations.original)) {
        Object.assign(payload, { [resource === 'criancas' ? 'responsaveis_ids' : 'criancas_ids']: relations.selected })
      }
    }
    if (hasEnrollments) {
      if (!enrollments || enrollments.error) { setError('Carregue as inscrições antes de salvar.'); return }
      const changed = enrollmentPayload(enrollments)
      if (changed !== null) Object.assign(payload, { [resource === 'criancas' ? 'atividades' : 'criancas']: changed })
    }
    if (record && !Object.keys(payload).length) { setError('Nenhum campo foi alterado.'); return }
    setSaving(true); setError('')
    try {
      await apiRequest(`/${resource}${record ? `/${encodeURIComponent(record.id)}` : ''}`, {
        method: record ? 'PATCH' : 'POST', body: JSON.stringify(payload),
      }, token)
      onSaved()
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Não foi possível salvar.') }
    finally { setSaving(false) }
  }

  return <Drawer title={record ? 'Editar cadastro' : 'Novo cadastro'} busy={saving} onClose={onCancel}>
    <form className="record-editor" onSubmit={submit} aria-label={record ? 'Editar cadastro' : 'Novo cadastro'}>
      {resource === 'usuarios' && !record && <p>Informe os dados para criar uma conta. O novo usuário poderá entrar com seu usuário e senha.</p>}
      <PersonFields resource={resource} prefix="edit" values={values} onChange={setValues} disabled={saving} editing={!!record} />
      {hasRelations && (resource === 'criancas' || resource === 'responsaveis') && record && <RelationshipSelector resource={resource} id={record.id} token={token} state={relations} onChange={setRelations} disabled={saving} />}
      {hasEnrollments && (resource === 'criancas' || resource === 'atividades') && <EnrollmentSelector resource={resource} id={record?.id} token={token} disabled={saving} state={enrollments} onChange={setEnrollments} />}
      {error && <p className="feedback error" role="alert">{error}</p>}
      <div className="record-actions drawer-actions"><button className="primary-button" type="submit" disabled={saving || (hasRelations && (!relations || !!relations.error)) || (hasEnrollments && (!enrollments || !!enrollments.error))}>{saving ? 'Salvando…' : 'Salvar'}</button><button className="secondary-button" type="button" onClick={onCancel} disabled={saving}>Cancelar</button></div>
    </form>
  </Drawer>
}
