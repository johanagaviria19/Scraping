"use client"
import { useState } from "react"

const JAVA_BASE = "http://localhost:8080"

export default function LoginPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [remember, setRemember] = useState(true)
  const [showPass, setShowPass] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const submit = async () => {
    setError(null)
    setLoading(true)
    try {
      if (mode === 'register') {
        if (!email || !password || password !== confirm) {
          setError('Verifica los campos');
          return
        }
        const r = await fetch(`${JAVA_BASE}/auth/register`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: email, password })
        })
        if (!(r.status === 201 || r.ok)) { setError(`HTTP ${r.status}`); return }
        setMode('login')
      } else {
        if (!email || !password) { setError('Verifica email y contraseña'); return }
        const r = await fetch(`${JAVA_BASE}/auth/login`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: email, password })
        })
        if (!r.ok) { setError(`HTTP ${r.status}`); return }
        const j = await r.json()
        const tok = j?.accessToken
        if (!tok) { setError('Token no recibido'); return }
        if (remember) localStorage.setItem('auth_token', tok)
        location.href = "/"
      }
    } catch (e: any) {
      setError(String(e?.message || e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth">
      <div className="auth-card">
        <h1>{mode === 'login' ? 'Bienvenido' : 'Crear Cuenta'}</h1>
        <p className="sub">{mode === 'login' ? 'Inicia sesión en tu cuenta' : 'Regístrate para empezar'}</p>

        <label className="lbl">Email</label>
        <div className="input icon">
          <span>✉️</span>
          <input type="email" placeholder="tu@email.com" value={email} onChange={e => setEmail(e.target.value)} />
        </div>

        <label className="lbl">Contraseña</label>
        <div className="input icon">
          <span>🔒</span>
          <input type={showPass ? 'text' : 'password'} placeholder="••••••" value={password} onChange={e => setPassword(e.target.value)} />
          <button className="icon-btn" onClick={() => setShowPass(v => !v)} title={showPass ? 'Ocultar' : 'Mostrar'}>👁️</button>
        </div>

        {mode === 'register' && (
          <>
            <label className="lbl">Confirmar Contraseña</label>
            <div className="input icon">
              <span>🔒</span>
              <input type={showPass ? 'text' : 'password'} placeholder="••••••" value={confirm} onChange={e => setConfirm(e.target.value)} />
            </div>
          </>
        )}

        {mode === 'login' && (
          <div className="row between">
            <label className="lbl"><input type="checkbox" checked={remember} onChange={e => setRemember(e.target.checked)} /> Recuérdame</label>
            <a className="link" href="#">¿Olvidaste tu contraseña?</a>
          </div>
        )}

        {error && <div className="error center">{error}</div>}

        <button className="btn primary wide" onClick={submit} disabled={loading}>{loading ? '...' : (mode === 'login' ? 'Iniciar Sesión' : 'Registrarse')}</button>

        <div className="divider"><span>o</span></div>
        <div className="row">
          <button className="btn" disabled>G Google</button>
          <button className="btn" disabled>G GitHub</button>
        </div>

        <div className="center foot">
          {mode === 'login' ? (
            <span>¿No tienes cuenta? <button className="link" onClick={() => setMode('register')}>Regístrate</button></span>
          ) : (
            <span>¿Ya tienes cuenta? <button className="link" onClick={() => setMode('login')}>Inicia sesión</button></span>
          )}
        </div>
      </div>
    </div>
  )
}