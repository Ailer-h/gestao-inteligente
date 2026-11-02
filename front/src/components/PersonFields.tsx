import { resources } from '../lib/resources'
import type { Resource } from '../lib/resources'

export default function PersonFields({ resource, values, onChange, disabled = false, prefix, editing = false, allowedRoles }: {
  resource: Resource; values: Record<string, string>; onChange: (values: Record<string, string>) => void
  disabled?: boolean; prefix: string; editing?: boolean; allowedRoles?: number[]
}) {
  function change(name: string, value: string) {
    const next = { ...values, [name]: value }
    if (name === 'frequenta_escola' && value === 'false') {
      next.nome_escola = ''; next.serie_ano = ''
    }
    onChange(next)
  }
  return <div className="editor-grid">{resources[resource].fields.filter(field => !editing || !field.createOnly).map(field => {
    const schoolDisabled = resource === 'criancas' && values.frequenta_escola === 'false' && ['nome_escola', 'serie_ano'].includes(field.name)
    const id = `${prefix}-${field.name}`
    return <div key={field.name} className="editor-field"><label htmlFor={id}>{field.label}{field.required ? ' *' : ''}</label>
      {field.type === 'select' ? <select id={id} value={values[field.name] ?? ''} required={field.required} disabled={disabled || schoolDisabled} onChange={event => change(field.name, event.target.value)}>
        <option value="">Selecione</option>{field.options?.filter(([value]) => field.name !== 'cargo' || !allowedRoles || allowedRoles.includes(Number(value))).map(([value, label]) => <option value={value} key={value}>{label}</option>)}
      </select> : <input id={id} type={field.type ?? 'text'} value={values[field.name] ?? ''} required={field.required} maxLength={field.maxLength} minLength={field.minLength} disabled={disabled || schoolDisabled} step={field.type === 'number' ? 1 : undefined}
        onChange={event => change(field.name, event.target.value)} />}
    </div>
  })}</div>
}
