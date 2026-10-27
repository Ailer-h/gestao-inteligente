import { useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'
import Dashboard from './Dashboard'

function EyeIcon({ open }: { open: boolean }) {
  return <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {open ? <><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" /><circle cx="12" cy="12" r="3" /></> : <><path d="m3 3 18 18M10.6 5.1 12 5c6.5 0 10 7 10 7a19 19 0 0 1-3 3.7M6.3 6.3A20 20 0 0 0 2 12s3.5 7 10 7a12 12 0 0 0 5.7-1.7M9.9 9.9a3 3 0 0 0 4.2 4.2" /></>}
  </svg>
}

function App() {
  const [showPassword, setShowPassword] = useState(false)
  const [loggedIn, setLoggedIn] = useState(false)
  const [message, setMessage] = useState('')

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setMessage('')
    setLoggedIn(true)
  }

  if (loggedIn) return <Dashboard onLogout={() => { setLoggedIn(false); setShowPassword(false) }} />

  return (
    <main className="login-page">
      <section className="form-panel" aria-labelledby="login-title">
        <a className="brand" href="./" aria-label="Projeto Girassol IPEFE — início">
          <img className="brand-logo" src="/projeto-girassol-ipefe.jpg" alt="Logo do Projeto Girassol IPEFE — Crianças Atípicas" />
          <span className="brand-name">Projeto Girassol<small>IPEFE · PORTAL INSTITUCIONAL</small></span>
        </a>

        <div className="login-content">
          <div className="eyebrow"><span /> BEM-VINDO DE VOLTA</div>
          <h1 id="login-title">Bem-vindo ao<br />Projeto Girassol<span>.</span></h1>
          <p className="intro">Acesse sua conta para continuar.</p>

          <form onSubmit={handleSubmit}>
            <label htmlFor="username">Usuário</label>
            <div className="input-wrap">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><circle cx="12" cy="8" r="3.5" /><path d="M5 21v-2a7 7 0 0 1 14 0v2" /></svg>
              <input id="username" name="username" autoComplete="username" placeholder="Digite seu usuário" required />
            </div>

            <label htmlFor="password">Senha</label>
            <div className="input-wrap">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" aria-hidden="true"><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3M12 15v2" /></svg>
              <input id="password" name="password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" placeholder="Digite sua senha" required />
              <button className="eye-button" type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'} aria-pressed={showPassword}><EyeIcon open={showPassword} /></button>
            </div>
            <div className="forgot-row"><button className="text-button" type="button" onClick={() => setMessage('Para recuperar sua senha, entre em contato com a administração do instituto.')}>Esqueci minha senha</button></div>
            <button className="submit-button" type="submit">Entrar <span aria-hidden="true">→</span></button>
            {message && <p className="form-message" role="status">{message}</p>}
          </form>
          <div className="access-note"><span aria-hidden="true">◇</span> Cuidado e acolhimento para crianças atípicas.</div>
        </div>
        <footer>© {new Date().getFullYear()} Projeto Girassol IPEFE<span>Todos os direitos reservados.</span></footer>
      </section>

      <aside className="institute-panel" aria-label="Projeto Girassol IPEFE — cuidado e acolhimento">
        <div className="panel-grid" aria-hidden="true" />
        <div className="panel-top"><span className="institution-tag"><span /> NOSSO INSTITUTO</span><span className="edition">PROJETO GIRASSOL IPEFE</span></div>
        <div className="orbit orbit-one" aria-hidden="true" /><div className="orbit orbit-two" aria-hidden="true" />
        <div className="institute-photo-wrap">
          <img className="institute-photo" src="/instituto-criancas.jpeg" alt="Crianças participando de uma atividade de pintura em grupo" />
        </div>
        <div className="panel-bottom"><span className="yellow-line" /><h2>Cuidar de cada criança.<br />Acolher cada história.</h2><p>Somos uma ONG dedicada ao cuidado de crianças atípicas.</p><div className="panel-bottom-line"><span>CUIDADO, RESPEITO E INCLUSÃO.</span><span aria-hidden="true">↗</span></div></div>
      </aside>
    </main>
  )
}

export default App




