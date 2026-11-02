import { useEffect, useState } from 'react'
import { apiRequest } from '../lib/api'
import { resources } from '../lib/resources'
import type { Resource } from '../lib/resources'

const keys: Resource[] = ['criancas', 'responsaveis', 'usuarios', 'atividades']
interface RankedActivity { id: number; nome: string; criancas_ativas: number }

export default function Overview({ token }: { token: string }) {
  const [counts, setCounts] = useState<Record<Resource, number> | null>(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [ranking, setRanking] = useState<RankedActivity[]>([])
  useEffect(() => {
    const controller = new AbortController()
    Promise.all([
      apiRequest<Record<Resource, number>>('/resumo', { signal: controller.signal }, token),
      apiRequest<RankedActivity[]>('/relatorios/atividades?limit=10', { signal: controller.signal }, token),
    ])
      .then(([data, activities]) => { if (!controller.signal.aborted) { setCounts(data); setRanking(activities) } })
      .catch(cause => { if (!controller.signal.aborted) setError(cause.message) })
    return () => controller.abort()
  }, [token, attempt])
  if (error) return <div className="feedback error" role="alert"><p>{error}</p><button className="secondary-button" onClick={() => { setError(''); setAttempt(value => value + 1) }}>Tentar novamente</button></div>
  if (!counts) return <p role="status">Carregando informações do instituto…</p>
  const largest = Math.max(1, ...ranking.map(item => item.criancas_ativas))
  return <>
    <section className="summary-grid" aria-label="Total de cadastros">{keys.map(key => <article className="stat-card" key={key}>
      <span className="placeholder-tag">Cadastros</span><span className="stat-value">{counts[key]}</span><h2>{resources[key].label}</h2>
    </article>)}</section>
    <section className="chart-card summary-chart" aria-label="Atividades com mais crianças"><div className="chart-heading"><div><h2>Atividades com mais crianças</h2><p>Até 10 atividades, ordenadas pelo número de crianças com inscrição ativa. Inscrições inativas e aguardando não entram na contagem.</p></div></div>
      {!ranking.length ? <p className="records-empty">Nenhuma atividade cadastrada.</p> : ranking.map((item, index) => <div className="summary-bar" key={item.id}><span>{index + 1}. {item.nome}</span><div><span style={{ width: `${item.criancas_ativas / largest * 100}%` }} /></div><strong aria-label={`${item.criancas_ativas} crianças ativas`}>{item.criancas_ativas}</strong></div>)}
    </section>
  </>
}
