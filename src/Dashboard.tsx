import { useEffect, useState } from 'react'
import './Dashboard.css'

const pages = ['Tela Inicial', 'Usuários', 'Alunos', 'Pais/Responsáveis', 'Formulário de cadastro'] as const
type Page = typeof pages[number]
type IconName = 'home' | 'users' | 'students' | 'family' | 'form' | 'menu' | 'exit' | 'chart' | 'cards' | 'table'
const THEME_STORAGE_KEY = 'girassol-ipefe-theme'
const VIEWS_STORAGE_KEY = 'girassol-ipefe-record-views'
const icons: IconName[] = ['home', 'users', 'students', 'family', 'form']

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

export default function Dashboard({ onLogout }: { onLogout: () => void }) {
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
        ['Usuários', 'Alunos', 'Pais/Responsáveis'].includes(key) &&
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
  const columns = page === 'Usuários' ? ['Nome', 'E-mail', 'Perfil', 'Status'] : page === 'Alunos' ? ['Nome', 'Responsável', 'Turma', 'Status'] : ['Nome', 'Contato', 'Aluno vinculado', 'Parentesco']

  return <div className={`dashboard-shell ${dark ? 'theme-dark' : 'theme-light'} ${expanded ? 'is-expanded' : 'is-collapsed'}`}>
    <aside className="sidebar" aria-label="Menu principal">
      <a href="#inicio" className="sidebar-brand" onClick={event => { event.preventDefault(); setPage('Tela Inicial') }} aria-label="Projeto Girassol IPEFE — Tela Inicial">
        <img src="/projeto-girassol-ipefe.jpg" alt="Logo do Projeto Girassol IPEFE" />
        <span>Projeto Girassol<small>IPEFE · INSTITUTO</small></span>
      </a>
      <div className="sidebar-controls"><button className="sidebar-toggle" type="button" onClick={() => setExpanded(!expanded)} aria-expanded={expanded} aria-controls="sidebar-navigation" aria-label={expanded ? 'Minimizar barra lateral' : 'Expandir barra lateral'} title={expanded ? 'Minimizar menu' : 'Expandir menu'}><Icon name="menu" /></button><button className="theme-toggle" type="button" onClick={() => setDark(!dark)} aria-label={dark ? 'Ativar tema claro' : 'Ativar tema escuro'} title={dark ? 'Ativar tema claro' : 'Ativar tema escuro'}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{dark ? <><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5 19 19M5 19l1.5-1.5M17.5 6.5 19 5" /></> : <path d="M21 13a9 9 0 0 1-10-10A9 9 0 1 0 21 13Z" />}</svg></button></div>
      <span className="nav-caption">PRINCIPAL</span>
      <nav id="sidebar-navigation">{pages.map((item, index) => <button key={item} type="button" className={`nav-item ${page === item ? 'active' : ''}`} onClick={() => setPage(item)} aria-current={page === item ? 'page' : undefined} aria-label={item} title={item}><Icon name={icons[index]} /><span>{item}</span></button>)}</nav>
      <div className="sidebar-footer"><div className="institute-note"><span className="institute-dot" /> Cuidado, respeito e inclusão</div><button className="nav-item logout" type="button" onClick={onLogout} aria-label="Sair" title="Sair"><Icon name="exit" /><span>Sair</span></button></div>
    </aside>
    <div className="dashboard-main">
      <header className="dashboard-header"><div><span className="header-institute">PROJETO GIRASSOL IPEFE</span><p>Portal institucional</p></div><span className="demo-badge"><span /> Ambiente de demonstração</span></header>
      <main className="dashboard-content" id="main-content">
        <div className="page-heading"><div><div className="dashboard-eyebrow">{page === 'Tela Inicial' ? 'VISÃO GERAL' : 'GESTÃO DO INSTITUTO'}</div><h1>{page}</h1><p>{page === 'Tela Inicial' ? 'Acompanhe as informações do instituto em um só lugar.' : 'Um espaço para organizar as informações do instituto.'}</p></div><span className="page-marker"><Icon name={icons[pages.indexOf(page)]} /></span></div>
        {page === 'Tela Inicial' ? <>
          <section className="overview-grid" aria-label="Estatísticas e gráfico do instituto">
            <div className="stat-grid">{[{ label: 'Alunos', icon: 'students' }, { label: 'Pais/Responsáveis', icon: 'family' }, { label: 'Usuários', icon: 'users' }].map((stat, index) => <article className="stat-card" key={stat.label}><div className="stat-card-top"><span className={`stat-icon tone-${index}`}><Icon name={stat.icon as IconName} /></span><span className="placeholder-tag">Sem dados</span></div><span className="stat-value" aria-label="Dados ainda não disponíveis">—</span><h2>{stat.label}</h2><p>Aguardando cadastros</p></article>)}</div>
            <article className="chart-card"><div className="chart-heading"><div><h2>Visão dos cadastros</h2><p>Acompanhe a evolução dos registros do instituto.</p></div><span className="placeholder-tag">Sem dados</span></div><div className="chart-placeholder"><div className="chart-grid" aria-hidden="true" /><div className="chart-empty"><span><Icon name="chart" /></span><h3>Os dados vão aparecer aqui</h3><p>O gráfico será preenchido quando houver registros.</p></div></div><div className="chart-legend"><span /> Cadastros do instituto</div></article>
          </section>
          <div className="dashboard-info"><span className="info-symbol" aria-hidden="true">i</span><p>Estamos preparando este espaço. As estatísticas e o gráfico são placeholders, sem dados reais.</p></div>
        </> : page !== 'Formulário de cadastro' ? <section className="records-section" aria-label={`Listagem de ${page}`}>
          <div className="records-toolbar"><span className="records-count">Nenhum registro</span><div className="view-switch" role="group" aria-label="Modo de visualização">{(['cards', 'table'] as const).map(mode => <button type="button" key={mode} onClick={() => setViews(previous => ({ ...previous, [page]: mode }))} aria-pressed={view === mode} className={view === mode ? 'selected' : ''}><Icon name={mode} /><span>{mode === 'cards' ? 'Cards' : 'Tabela'}</span></button>)}</div></div>
          {view === 'table' ? <div className="records-table-wrap"><table className="records-table"><caption className="sr-only">{page} — visualização em tabela</caption><thead><tr>{columns.map(column => <th key={column} scope="col">{column}</th>)}</tr></thead><tbody><tr><td colSpan={columns.length}><div className="records-empty"><Icon name={icons[pages.indexOf(page)]} /><h2>Nenhum cadastro por enquanto</h2><p>Os registros de {page.toLocaleLowerCase('pt-BR')} aparecerão nesta tabela.</p></div></td></tr></tbody></table></div> : <div className="records-empty records-card-empty"><Icon name={icons[pages.indexOf(page)]} /><h2>Nenhum cadastro por enquanto</h2><p>Os registros de {page.toLocaleLowerCase('pt-BR')} aparecerão aqui em cards.</p></div>}
        </section> : <section className="page-placeholder"><span className="empty-page-icon"><Icon name={icons[pages.indexOf(page)]} /></span><h2>{page}</h2><p>Esta tela será preparada na próxima etapa.</p><span className="placeholder-tag">Em construção · sem dados</span></section>}
        <footer className="dashboard-footer"><span>Projeto Girassol IPEFE</span><span>Cuidar de cada criança. Acolher cada história.</span></footer>
      </main>
    </div>
  </div>
}





