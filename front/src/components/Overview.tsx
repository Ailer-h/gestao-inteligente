import { useEffect, useState } from 'react'
import { apiRequest } from '../lib/api'
import { resources } from '../lib/resources'
import type { Resource } from '../lib/resources'

const keys: Resource[] = ['criancas', 'responsaveis', 'usuarios', 'atividades']
interface RankedActivity { id: number; nome: string; criancas_ativas: number }
const COLOR_MODE_KEY = 'girassol-ranking-colorblind'

export default function Overview({ token }: { token: string }) {
  const [colorblind, setColorblind] = useState(() => {
    try { return localStorage.getItem(COLOR_MODE_KEY) === 'true' } catch { return false }
  })
  useEffect(() => {
    try { localStorage.setItem(COLOR_MODE_KEY, String(colorblind)) } catch { /* Keep the control usable without storage. */ }
  }, [colorblind])
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
  const smallest = Math.min(...ranking.map(item => item.criancas_ativas))
  return <>
    <section className="summary-grid" aria-label="Total de cadastros">{keys.map(key => <article className="stat-card" key={key}>
      <span className="placeholder-tag">Cadastros</span><span className="stat-value">{counts[key]}</span><h2>{resources[key].label}</h2>
    </article>)}</section>
    <section className={`chart-card summary-chart${colorblind ? ' ranking-colorblind' : ''}`} aria-label="Atividades com mais crianças"><div className="chart-heading"><div><h2>Atividades com mais crianças</h2><p>Até 10 atividades, ordenadas pelo número de crianças com inscrição ativa. Inscrições inativas e aguardando não entram na contagem.</p></div>
      <button type="button" className="secondary-button ranking-mode" aria-pressed={colorblind} onClick={() => setColorblind(previous => !previous)}>Modo daltônico: {colorblind ? 'ativado' : 'desativado'}</button>
      </div>
      {colorblind && <p className="ranking-explanation" role="status">Modo daltônico ativo: Top 3 em azul com marcas verticais, intermediárias em ocre com listras e menor participação em roxo com pontos.</p>}
      <p className="ranking-explanation">As três primeiras posições têm destaque. Após elas, a menor contagem entre as atividades exibidas recebe a indicação de menor participação, incluindo empates.</p>
      <ul className="ranking-legend" aria-label="Legenda do ranking">
        <li className="ranking-top"><span aria-hidden="true">★</span> Top 3</li>
        <li className="ranking-middle"><span aria-hidden="true">◆</span> Intermediária</li>
        <li className="ranking-low"><span aria-hidden="true">▼</span> Menor participação</li>
      </ul>
      {!ranking.length ? <p className="records-empty">Nenhuma atividade cadastrada.</p> : ranking.map((item, index) => {
        const tier = index < 3 ? 'top' : item.criancas_ativas === smallest ? 'low' : 'middle'
        const label = tier === 'top' ? 'Top 3' : tier === 'low' ? 'Menor participação' : 'Intermediária'
        const symbol = tier === 'top' ? '★' : tier === 'low' ? '▼' : '◆'
        return <div className={`summary-bar ranking-${tier}`} key={item.id}>
          <span>{index + 1}. {item.nome}<small className="ranking-category"><span aria-hidden="true">{symbol} </span>{label}</small></span>
          <div aria-hidden="true"><span style={{ width: `${item.criancas_ativas / largest * 100}%` }} /></div>
          <strong aria-label={`${item.criancas_ativas} crianças ativas`}>{item.criancas_ativas}</strong>
        </div>
      })}
    </section>
  </>
}
