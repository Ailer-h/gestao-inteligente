import { useEffect, useState } from 'react'
import './Dashboard.css'
import ResourceManager from './components/ResourceManager'
import Overview from './components/Overview'
import type { Resource } from './lib/resources'
import { apiRequest } from './lib/api'
import FamilyRegistration from './components/FamilyRegistration'

const pages = ['Tela Inicial', 'Usuários', 'Alunos', 'Pais/Responsáveis', 'Atividades', 'Formulário de cadastro'] as const
type Page = typeof pages[number]
type IconName = 'home' | 'users' | 'students' | 'family' | 'form' | 'menu' | 'exit' | 'chart' | 'cards' | 'table'
const THEME_STORAGE_KEY = 'girassol-ipefe-theme'
const VIEWS_STORAGE_KEY = 'girassol-ipefe-record-views'
const icons: IconName[] = ['home', 'users', 'students', 'family', 'chart', 'form']

function Icon({ name }: { name: IconName }) {
  const paths = {
    cards: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
    table: <><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M3 9h18M3 14h18M10 9v11" /></>,
    home: <><path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z" /></>,
    users: <><circle cx="9" cy="8" r="3" /><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6M18 15a5 5 0 0 1 3 5" /></>,
    students: <><path d="m2 8 10-5 10 5-10 5ZM6 10v6c3 3 9 3 12 0v-6M22 8v7" /><path d="M8 21h8" /></>,
    family: <><circle cx="6" cy="6" r="2" /><circle cx="18" cy="6" r="2" /><circle cx="12" cy="13" r="2" /><path d="M2 18v-5a4 4 0 0 1 7-2M22 18v-5a4 4 0 0 0-7-2M8 22v-2a4 4 0 0 1 8 0v2" /></>,
    form: <><rect x="5" y="4" width="14" height="18" rx="2" /><path d="M9 4V2h6v2M9 10h6M9 14h6M9 18h3" /></>,
    menu: <><path d="M4 5h16M4 12h16M4 19h16" /></>,
    exit: <><path d="M10 4H4v16h6M9 12h12m-4-4 4 4-4 4" /></>,
    chart: <><path d="M4 3v18h17M8 16v-4M13 16V8M18 16V5" /></>,
  }
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}

export default function Dashboard({ onLogout, token, username }: { onLogout: () => void; token: string; username: string }) {
  const [cargo, setCargo] = useState<number | null>(null)
  useEffect(() => {
    const controller = new AbortController()
    apiRequest<{ cargo: number }>('/auth/me', { signal: controller.signal }, token)
      .then(profile => setCargo(profile.cargo)).catch(() => {})
    return () => controller.abort()
  }, [token])
  const [expanded, setExpanded] = useState(false)
  const [dark, setDark] = useState(() => {
    try {
      return localStorage.getItem(THEME_STORAGE_KEY) === 'dark'
    } catch {
      return false
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, dark ? 'dark' : 'light')
    } catch {
      // Keep the theme switch usable when browser storage is unavailable.
    }
  }, [dark])
  const [page, setPage] = useState<Page>('Tela Inicial')
  const [views, setViews] = useState<Record<string, 'cards' | 'table'>>(() => {
    try {
      const saved: unknown = JSON.parse(localStorage.getItem(VIEWS_STORAGE_KEY) ?? '{}')
      if (!saved || typeof saved !== 'object' || Array.isArray(saved)) return {}
      return Object.fromEntries(Object.entries(saved).filter(([key, value]) =>
        ['Usuários', 'Alunos', 'Pais/Responsáveis', 'Atividades'].includes(key) &&
        (value === 'cards' || value === 'table')
      ))
    } catch {
      return {}
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(VIEWS_STORAGE_KEY, JSON.stringify(views))
    } catch {
      // Keep view selection usable when browser storage is unavailable.
    }
  }, [views])
  const view = views[page] ?? 'cards'
  const [registrationOpen, setRegistrationOpen] = useState(false)
  const [registrationNotice, setRegistrationNotice] = useState('')
  const [registrationVersion, setRegistrationVersion] = useState(0)
  const resource: Resource = page === 'Usuários' ? 'usuarios' : page === 'Alunos' ? 'criancas' : page === 'Atividades' ? 'atividades' : 'responsaveis'

  return <div className={`dashboard-shell ${dark ? 'theme-dark' : 'theme-light'} ${expanded ? 'is-expanded' : 'is-collapsed'}`}>
    <aside className="sidebar" aria-label="Menu principal">
      <a href="#inicio" className="sidebar-brand" onClick={event => { event.preventDefault(); setPage('Tela Inicial') }} aria-label="Projeto Girassol IPEFE — Tela Inicial">
        <img src="/projeto-girassol-ipefe.jpg" alt="Logo do Projeto Girassol IPEFE" />
        <span>Projeto Girassol<small>IPEFE · INSTITUTO</small></span>
      </a>
      <div className="sidebar-controls"><button className="sidebar-toggle" type="button" onClick={() => setExpanded(!expanded)} aria-expanded={expanded} aria-controls="sidebar-navigation" aria-label={expanded ? 'Minimizar barra lateral' : 'Expandir barra lateral'} title={expanded ? 'Minimizar menu' : 'Expandir menu'}><Icon name="menu" /></button><button className="theme-toggle" type="button" onClick={() => setDark(!dark)} aria-label={dark ? 'Ativar tema claro' : 'Ativar tema escuro'} title={dark ? 'Ativar tema claro' : 'Ativar tema escuro'}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{dark ? <><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5 19 19M5 19l1.5-1.5M17.5 6.5 19 5" /></> : <path d="M21 13a9 9 0 0 1-10-10A9 9 0 1 0 21 13Z" />}</svg></button></div>
      <span className="nav-caption">PRINCIPAL</span>
      <nav id="sidebar-navigation">{pages.map((item, index) => index === 1 && (cargo === null || cargo === 3) ? null : <button key={item} type="button" className={`nav-item ${page === item ? 'active' : ''}`} onClick={() => { if (item === 'Formulário de cadastro') { setRegistrationNotice(''); setRegistrationOpen(true) } else setPage(item) }} aria-current={page === item ? 'page' : undefined} aria-label={item} title={item}><Icon name={icons[index]} /><span>{item}</span></button>)}</nav>
      <div className="sidebar-footer"><div className="institute-note"><span className="institute-dot" /> Cuidado, respeito e inclusão</div><button className="nav-item logout" type="button" onClick={onLogout} aria-label="Sair" title="Sair"><Icon name="exit" /><span>Sair</span></button></div>
    </aside>
    <div className="dashboard-main">
      <header className="dashboard-header"><div><span className="header-institute">PROJETO GIRASSOL IPEFE</span><p>Portal institucional</p></div><span className="demo-badge"><span /> {username}</span></header>
      <main className="dashboard-content" id="main-content">
        <div className="page-heading"><div><div className="dashboard-eyebrow">{page === 'Tela Inicial' ? 'VISÃO GERAL' : 'GESTÃO DO INSTITUTO'}</div><h1>{page}</h1><p>{page === 'Tela Inicial' ? 'Acompanhe as informações do instituto em um só lugar.' : 'Um espaço para organizar as informações do instituto.'}</p></div><span className="page-marker"><Icon name={icons[pages.indexOf(page)]} /></span></div>
        {registrationNotice && <p className="feedback success" role="status">{registrationNotice}</p>}
        {page === 'Tela Inicial' ? <Overview key={registrationVersion} token={token} /> : <ResourceManager key={`${resource}-${registrationVersion}`} resource={resource} cargo={cargo} token={token} view={view} onViewChange={mode => setViews(previous => ({ ...previous, [page]: mode }))} />}
        {registrationOpen && <FamilyRegistration token={token} onClose={() => setRegistrationOpen(false)} onSaved={() => { setRegistrationOpen(false); setRegistrationNotice('Cadastro e vínculos confirmados.'); setRegistrationVersion(value => value + 1) }} />}
        <footer className="dashboard-footer"><span>Projeto Girassol IPEFE</span><span>Cuidar de cada criança. Acolher cada história.</span></footer>
      </main>
    </div>
  </div>
}





