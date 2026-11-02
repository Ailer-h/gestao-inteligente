import { useState } from 'react'
import type { FormEvent } from 'react'
import { apiRequest } from '../lib/api'
import { initialValues, toPayload } from '../lib/resources'
import Drawer from './Drawer'
import PersonFields from './PersonFields'

type Person = { key: string; values: Record<string, string> }
const newPerson = (resource: 'criancas' | 'responsaveis'): Person => ({ key: crypto.randomUUID(), values: initialValues(resource) })

export default function FamilyRegistration({ token, onClose, onSaved }: {
  token: string; onClose: () => void; onSaved: () => void
}) {
  const [responsaveis, setResponsaveis] = useState<Person[]>(() => [newPerson('responsaveis')])
  const [criancas, setCriancas] = useState<Person[]>(() => [newPerson('criancas')])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving) return
    setSaving(true); setError('')
    try {
      await apiRequest('/cadastros', { method: 'POST', body: JSON.stringify({
        responsaveis: responsaveis.map(item => toPayload('responsaveis', item.values)),
        criancas: criancas.map(item => toPayload('criancas', item.values)),
      }) }, token)
      onSaved()
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Não foi possível confirmar o cadastro.') }
    finally { setSaving(false) }
  }
  return <Drawer title="Cadastro geral" busy={saving} onClose={onClose}>
    <form className="record-editor family-form" onSubmit={submit}>
      <p>Adicione pelo menos um responsável e uma criança. Todos os responsáveis deste cadastro serão vinculados a todas as crianças informadas.</p>
      <section aria-label="Responsáveis do cadastro"><h3>Responsável <small>obrigatório</small></h3>
        {responsaveis.map((person, index) => <fieldset key={person.key}><legend>Responsável {index + 1}</legend>
          <PersonFields resource="responsaveis" prefix={`responsavel-${person.key}`} values={person.values} disabled={saving} onChange={values => setResponsaveis(previous => previous.map(item => item.key === person.key ? { ...item, values } : item))} />
          {responsaveis.length > 1 && <button type="button" className="danger-button" disabled={saving} onClick={() => setResponsaveis(previous => previous.filter(item => item.key !== person.key))}>Remover responsável {index + 1}</button>}
        </fieldset>)}
        <button type="button" className="secondary-button" disabled={saving || responsaveis.length >= 20} onClick={() => setResponsaveis(previous => [...previous, newPerson('responsaveis')])}>+ Adicionar responsável</button>
      </section>
      <section aria-label="Crianças do cadastro"><h3>Criança</h3>
        {criancas.map((person, index) => <fieldset key={person.key}><legend>Criança {index + 1}</legend>
          <PersonFields resource="criancas" prefix={`crianca-${person.key}`} values={person.values} disabled={saving} onChange={values => setCriancas(previous => previous.map(item => item.key === person.key ? { ...item, values } : item))} />
          {criancas.length > 1 && <button type="button" className="danger-button" disabled={saving} onClick={() => setCriancas(previous => previous.filter(item => item.key !== person.key))}>Remover criança {index + 1}</button>}
        </fieldset>)}
        <button type="button" className="secondary-button" disabled={saving || criancas.length >= 20} onClick={() => setCriancas(previous => [...previous, newPerson('criancas')])}>+ Adicionar criança</button>
      </section>
      {error && <p className="feedback error" role="alert">{error}</p>}
      <div className="record-actions drawer-actions"><button type="submit" className="primary-button" disabled={saving}>{saving ? 'Confirmando…' : 'Confirmar'}</button><button type="button" className="secondary-button" onClick={onClose} disabled={saving}>Cancelar</button></div>
    </form>
  </Drawer>
}
