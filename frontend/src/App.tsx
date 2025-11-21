import { useEffect, useMemo, useState } from 'react'

type Item = {
  title: string | null
  url: string | null
  image?: string | null
  price?: number | null
  discount_price?: number | null
  rating?: number | null
  rating_count?: number | null
  sold?: number | null
  description?: string | null
  reviews?: Array<{ title?: string | null; content?: string | null; rate?: number | null; date?: string | null }>
}

type ApiResponse = {
  keyword: string
  count: number
  items: Item[]
}

type HistogramBucket = { min: number; max: number; count: number }
type Analysis = {
  summary: { count: number; price: { min: number | null; max: number | null; avg: number | null; median: number | null }; rating: { min: number | null; max: number | null; avg: number | null }; discount_count: number }
  histogram_price: HistogramBucket[]
  sentiment: { count: number; positive: number | null; negative: number | null; neutral?: number | null; avg_score: number | null }
  reviews_report?: {
    products: Array<{ title: string | null; avg_rating: number; reviews_count: number; positive_pct: number; url?: string | null }>
    ranking: Array<{ title: string | null; avg_rating: number; reviews_count: number; positive_pct: number; url?: string | null }>
    top3: Array<{ title: string | null; avg_rating: number; reviews_count: number; positive_pct: number; url?: string | null }>
    star_product?: { title: string | null; avg_rating: number; reviews_count: number; positive_pct: number; url?: string | null } | null
    best_reviews_by_product: Array<{ title: string | null; reviews: Array<{ rate: number | null; date?: string | null; content: string }> }>
  }
}

type ApiResponseWithAnalysis = ApiResponse & { analysis?: Analysis }

const API_BASE = 'http://127.0.0.1:8000'
const JAVA_BASE = 'http://localhost:8080'

const IconMail = (props: any) => (
  <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" {...props}>
    <rect x="3" y="5" width="18" height="14" rx="2"/>
    <path d="M3 7l9 6 9-6"/>
  </svg>
)

const IconLock = (props: any) => (
  <svg width={22} height={22} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" {...props}>
    <rect x="5" y="11" width="14" height="9" rx="2"/>
    <path d="M7 11V8a5 5 0 0 1 10 0v3"/>
    <circle cx="12" cy="15" r="1.5"/>
  </svg>
)

const IconEye = (props: any) => (
  <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7z"/>
    <circle cx="12" cy="12" r="3"/>
  </svg>
)

const IconEyeOff = (props: any) => (
  <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7z"/>
    <path d="M3 3l18 18"/>
    <circle cx="12" cy="12" r="3"/>
  </svg>
)

const IconCart = (props: any) => (
  <svg width={22} height={22} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" {...props}>
    <circle cx="9" cy="20" r="2"/>
    <circle cx="17" cy="20" r="2"/>
    <path d="M2 3h3l2 12h11l2-8H6"/>
  </svg>
)


const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/
const isValidEmail = (s: string) => EMAIL_REGEX.test(String(s || '').trim().toLowerCase())
const PASSWORD_POLICY = {
  minLength: Number(import.meta.env?.VITE_PW_MIN ?? 8),
  requireUpper: String(import.meta.env?.VITE_PW_UPPER ?? 'true') === 'true',
  requireLower: String(import.meta.env?.VITE_PW_LOWER ?? 'true') === 'true',
  requireNumber: String(import.meta.env?.VITE_PW_NUMBER ?? 'true') === 'true',
  requireSymbol: String(import.meta.env?.VITE_PW_SYMBOL ?? 'true') === 'true',
}
const passwordIssues = (s: string) => {
  const issues: string[] = []
  if ((s || '').length < PASSWORD_POLICY.minLength) issues.push(`Mínimo ${PASSWORD_POLICY.minLength} caracteres`)
  if (PASSWORD_POLICY.requireUpper && !/[A-Z]/.test(s)) issues.push('Una mayúscula')
  if (PASSWORD_POLICY.requireLower && !/[a-z]/.test(s)) issues.push('Una minúscula')
  if (PASSWORD_POLICY.requireNumber && !/\d/.test(s)) issues.push('Un número')
  if (PASSWORD_POLICY.requireSymbol && !/[\W_]/.test(s)) issues.push('Un símbolo')
  return issues
}
const passwordScore = (s: string) => {
  let score = 0
  if (s.length >= PASSWORD_POLICY.minLength) score++
  if (/[A-Z]/.test(s)) score++
  if (/[a-z]/.test(s)) score++
  if (/\d/.test(s)) score++
  if (/[\W_]/.test(s)) score++
  if (s.length >= PASSWORD_POLICY.minLength + 4) score++
  return Math.min(6, score)
}

export default function App() {
  const [source, setSource] = useState('telefono')
  const [isUrl, setIsUrl] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<ApiResponse | null>(null)
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [token, setToken] = useState<string | null>(null)
  const [priceMin, setPriceMin] = useState<number>(0)
  const [priceMax, setPriceMax] = useState<number>(0)
  const [ratingMin, setRatingMin] = useState<number>(0)
  const [ratingMax, setRatingMax] = useState<number>(5)
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [remember, setRemember] = useState(true)
  const [showPwd, setShowPwd] = useState(false)
  const [showPwdReg2, setShowPwdReg2] = useState(false)
  const [authErrors, setAuthErrors] = useState<{ email?: string; password?: string; confirm?: string; general?: string }>({})
  const [authLoading, setAuthLoading] = useState(false)
  const [attempts, setAttempts] = useState(0)
  const [lockUntil, setLockUntil] = useState<number | null>(null)
  const pwScore = useMemo(() => passwordScore(password), [password])
  const pwIssues = useMemo(() => passwordIssues(password), [password])
  useEffect(() => { try { document.title = 'smartmarket-ai' } catch {} }, [])
  const priceMaxBound = useMemo(() => {
    const items = data?.items || []
    const prices = items.map(it => Number(it.price || 0)).filter(v => v > 0)
    const pmax = prices.length ? Math.max(...prices) : 5
    return Math.max(5, pmax)
  }, [data?.items])

  const canSearch = useMemo(() => source.trim().length > 0, [source])


  const formatCOP = (v?: number | null) => {
    const n = Number(v || 0)
    if (!n || n <= 0) return ''
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n)
  }


  useEffect(() => {
    const ls = typeof window !== 'undefined' ? window.localStorage.getItem('accessToken') : null
    const ss = typeof window !== 'undefined' ? window.sessionStorage.getItem('accessToken') : null
    const stored = ls || ss
    if (stored) setToken(stored)
    const items = data?.items || []
    const prices = items.map(it => Number(it.price || 0)).filter(v => v > 0)
    const ratings = items.map(it => Number(it.rating || 0)).filter(v => v >= 0)
    const pmin = prices.length ? Math.min(...prices) : 0
    const pmax = prices.length ? Math.max(...prices) : 0
    const rmin = ratings.length ? Math.min(...ratings) : 0
    const rmax = ratings.length ? Math.max(...ratings) : 5
    setPriceMin(pmin)
    setPriceMax(pmax)
    setRatingMin(rmin)
    setRatingMax(rmax)
  }, [data?.items])

  const filteredItems = useMemo(() => {
    const items = data?.items || []
    return items.filter(it => {
      const p = Number(it.price || 0)
      const r = Number(it.rating || 0)
      const okP = p === 0 ? true : (p >= Math.min(priceMin, priceMax) && p <= Math.max(priceMin, priceMax))
      const okR = r >= Math.min(ratingMin, ratingMax) && r <= Math.max(ratingMin, ratingMax)
      return okP && okR
    })
  }, [data?.items, priceMin, priceMax, ratingMin, ratingMax])

  const runSearch = async () => {
    if (!canSearch) return
    setLoading(true)
    setError(null)
    try {
      const endpoint = isUrl ? '/from-url_with_analysis' : '/search_cached_with_analysis'
      const body = isUrl
        ? { url: source }
        : { keyword: source }
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = (await res.json()) as ApiResponseWithAnalysis
      try {
        await fetch(`${JAVA_BASE}/api/data`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(json),
        })
      } catch {}
      setData(json)
      setAnalysis(json.analysis ?? null)
      if (token) {
        const params = new URLSearchParams()
        if (!isUrl && source) params.append('keyword', source)
        const listRes = await fetch(`${JAVA_BASE}/api/products?${params.toString()}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (listRes.ok) {
          const page = await listRes.json()
          const items: Item[] = (page?.content ?? []).map((p: any) => ({
            title: p.title,
            url: p.url,
            image: p.image,
            price: p.price,
            discount_price: p.discount_price,
            rating: p.rating,
            rating_count: p.rating_count,
            sold: p.sold,
            description: p.description,
          }))
          setData({ keyword: source, count: items.length, items })
        }
      }
    } catch (e: any) {
      setError(String(e?.message || e))
    } finally {
      setLoading(false)
    }
  }

  

  const login = async () => {
    setError(null)
    setAuthErrors({})
    const email = String(username || '').trim().toLowerCase()
    const pwd = String(password || '').trim()
    if (lockUntil && Date.now() < lockUntil) { setAuthErrors({ general: 'Demasiados intentos. Inténtalo en 1 minuto.' }); return }
    if (!isValidEmail(email)) { setAuthErrors({ email: 'Email inválido' }); return }
    if (pwd.length < 6) { setAuthErrors({ password: 'Contraseña demasiado corta' }); return }
    setAuthLoading(true)
    const res = await fetch(`${JAVA_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: email, password: pwd }),
    })
    if (!res.ok) {
      let msg = 'Error al iniciar sesión'
      try { const j = await res.json(); msg = String(j?.message || msg) } catch {}
      if (res.status === 401) msg = 'Email o contraseña inválidos'
      if (res.status === 429) msg = 'Demasiados intentos. Espera un momento.'
      setAuthErrors({ general: msg })
      const n = attempts + 1
      setAttempts(n)
      if (n >= 5) setLockUntil(Date.now() + 60_000)
      setUsername('')
      setPassword('')
      setConfirmPassword('')
      setShowPwd(false)
      
      setShowPwdReg2(false)
      setAuthLoading(false)
      return
    }
    const json = await res.json()
    setToken(json?.accessToken || null)
    try {
      if (remember) {
        window.localStorage.setItem('accessToken', json?.accessToken || '')
      } else {
        window.sessionStorage.setItem('accessToken', json?.accessToken || '')
      }
    } catch {}
    setAuthLoading(false)
  }

  const logout = () => {
    setToken(null)
    try {
      window.localStorage.removeItem('accessToken')
      window.sessionStorage.removeItem('accessToken')
    } catch {}
    setUsername('')
    setPassword('')
    setConfirmPassword('')
    setShowPwd(false)
    
    setShowPwdReg2(false)
    
  }

  

  if (!token) {
    return (
      <>
        <div className="topbar">
          <div className="brand">
            <IconCart />
            <span className="brand-title">smartmarket-ai</span>
          </div>
        </div>
        <div className="login-screen">
          <div className="auth-card">
          <div className="lock-badge"><IconLock /></div>
          <div className="auth-title">{authMode === 'login' ? 'Bienvenido' : 'Crear Cuenta'}</div>
          <div className="subtitle">{authMode === 'login' ? 'Inicia sesión en tu cuenta' : 'Regístrate para empezar'}</div>
          {authErrors.general && <div className="error">{authErrors.general}</div>}
          <div className="label">Email</div>
          <div className="input-group">
            <div className="input-icon"><IconMail /></div>
            <input className="input-field" placeholder="tu@email.com" value={username} onChange={(e) => setUsername(e.target.value)} aria-invalid={!!authErrors.email} aria-describedby="error-email" />
          </div>
          {authErrors.email && <div id="error-email" className="error-text">{authErrors.email}</div>}
          <div className="label">Contraseña</div>
          <div className="input-group">
            <div className="input-icon"><IconLock /></div>
            <input className="input-field" placeholder="••••••••" type={showPwd ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} aria-invalid={!!authErrors.password} aria-describedby="error-password" />
            <button type="button" className="visibility-toggle" aria-label="Mostrar u ocultar contraseña" onClick={() => setShowPwd(v => !v)}>{showPwd ? <IconEyeOff /> : <IconEye />}</button>
          </div>
          {authErrors.password && <div id="error-password" className="error-text">{authErrors.password}</div>}
          {authMode === 'register' && (
            <div className="pw-meter">
              {[0,1,2,3].map(i => (
                <div key={i} className={`pw-seg ${pwScore > i ? 'active' : ''}`} />
              ))}
              <div className="pw-label">{pwScore <= 1 ? 'Débil' : pwScore === 2 ? 'Media' : pwScore === 3 ? 'Buena' : 'Fuerte'}</div>
            </div>
          )}
          {authMode === 'register' && pwIssues.length > 0 && (
            <div className="pw-tips">Debe incluir: {pwIssues.join(', ')}</div>
          )}
          {authMode === 'register' && (
            <>
              <div className="label">Confirmar Contraseña</div>
              <div className="input-group">
                <div className="input-icon"><IconLock /></div>
                <input className="input-field" placeholder="••••••••" type={showPwdReg2 ? 'text' : 'password'} value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} aria-invalid={!!authErrors.confirm} aria-describedby="error-confirm" />
                <button type="button" className="visibility-toggle" aria-label="Mostrar u ocultar confirmación" onClick={() => setShowPwdReg2(v => !v)}>{showPwdReg2 ? <IconEyeOff /> : <IconEye />}</button>
              </div>
              {authErrors.confirm && <div id="error-confirm" className="error-text">{authErrors.confirm}</div>}
            </>
          )}
          {authMode === 'login' && (
            <div className="row between" style={{ marginTop: 6 }}>
              <label className="checkbox">
                <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
                <span>Recuérdame</span>
              </label>
              <button className="link accent" onClick={() => setAuthErrors({ general: 'Recuperación de contraseña próximamente' })}>¿Olvidaste tu contraseña?</button>
            </div>
          )}
          {authMode === 'login' ? (
            <button className="btn accent" onClick={login} disabled={authLoading || !isValidEmail(String(username)) || String(password).length < 6}>Iniciar Sesión</button>
          ) : (
            <button className="btn accent" onClick={async () => {
              setAuthErrors({})
              const email = String(username || '').trim().toLowerCase()
              const pwd = String(password || '').trim()
              const conf = String(confirmPassword || '').trim()
              if (!isValidEmail(email)) { setAuthErrors({ email: 'Email inválido' }); return }
              const issues = passwordIssues(pwd)
              if (issues.length) { setAuthErrors({ password: `La contraseña debe tener: ${issues.join(', ')}` }); return }
              if (pwd !== conf) { setAuthErrors({ confirm: 'Las contraseñas no coinciden' }); return }
              setAuthLoading(true)
              const res = await fetch(`${JAVA_BASE}/auth/register`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: email, password: pwd }),
              })
              if (!res.ok && res.status !== 201) {
                let msg = 'No se pudo registrar'
                try { const j = await res.json(); msg = String(j?.message || msg) } catch {}
                if (res.status === 409) msg = 'Email ya registrado'
                if (res.status === 422) msg = 'Datos inválidos'
                setAuthErrors({ general: msg })
                setAuthLoading(false)
                return
              }
              setAuthLoading(false)
              setAuthMode('login')
              setAuthErrors({ general: 'Registro exitoso. Inicia sesión.' })
            }} disabled={authLoading}>Registrarse</button>
          )}
          
          <div className="row center" style={{ marginTop: 8 }}>
            <span className="lbl">{authMode === 'login' ? '¿No tienes cuenta?' : '¿Ya tienes cuenta?'}</span>
            <button className="link accent" onClick={() => setAuthMode(m => m === 'login' ? 'register' : 'login')}>{authMode === 'login' ? 'Regístrate' : 'Inicia sesión'}</button>
          </div>
        </div>
        </div>
      </>
    )
  }

  return (
    <>
      <div className="topbar">
        <div className="brand">
          <IconCart />
          <span className="brand-title">smartmarket-ai</span>
        </div>
      </div>
      <div className="dashboard">
      <div className="sidebar">
        <div className="panel">
          <div className="panel-title">Búsqueda</div>
          <label className="row">
            <input type="checkbox" checked={isUrl} onChange={(e) => setIsUrl(e.target.checked)} />
            <span>Usar URL</span>
          </label>
          <input
            value={source}
            onChange={(e) => setSource(e.target.value)}
            placeholder={isUrl ? 'https://listado.mercadolibre.com.co/...' : 'palabra clave'}
            className="input"
          />
          <button className="btn primary" onClick={runSearch} disabled={!canSearch || loading}>
            {loading ? 'Buscando...' : 'Buscar y actualizar datos'}
          </button>
        </div>
      </div>
      <div className="main">
        <div className="header">
          <div className="title">Análisis de productos</div>
          <div className="auth">
            <button className="btn" onClick={logout}>Cerrar sesión</button>
          </div>
        </div>

        <div className="panel">
          <div className="row between">
            <div className="lbl">Rango de precio</div>
            <div className="lbl">{formatCOP(Math.min(priceMin, priceMax))} — {formatCOP(Math.max(priceMin, priceMax))}</div>
          </div>
          <div className="range">
            <input type="range" min={0} max={priceMaxBound} step={10000} value={priceMax} onChange={(e) => setPriceMax(Number(e.target.value))} />
          </div>
          <div className="row between">
            <div className="lbl">Rango de calificación</div>
            <div className="lbl">{Math.min(ratingMin, ratingMax).toFixed(2)} — {Math.max(ratingMin, ratingMax).toFixed(2)}</div>
          </div>
          <div className="range">
            <input type="range" min={0} max={5} step={0.1} value={ratingMin} onChange={(e) => setRatingMin(Number(e.target.value))} />
          </div>
        </div>

        {error && <div className="error">{error}</div>}

        {data && (
          <div className="panel">
            <div className="panel-title">Tabla de productos</div>
            <table className="table">
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Precio</th>
                  <th>Rating</th>
                  <th>Opiniones</th>
                  <th>Vendidos</th>
                  <th>Enlace</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((it, idx) => (
                  <tr key={idx}>
                    <td className="title">
                      {it.image ? <img src={it.image} alt="" /> : null}
                      <span>{it.title}</span>
                    </td>
                    <td>{formatCOP(Number(it.price || 0))}</td>
                    <td>{it.rating ?? ''}</td>
                    <td>{(it.rating_count ?? (it.reviews ? it.reviews.length : undefined)) ?? ''}</td>
                    <td>{it.sold ?? ''}</td>
                    <td>{it.url ? <a href={it.url} target="_blank" rel="noreferrer">Abrir</a> : ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {analysis && (
          <div className="results">
            <div className="panel">
              <div className="panel-title">Análisis</div>
              <div className="row wrap">
                <div className="lbl">Items: {analysis.summary.count}</div>
                <div className="lbl">Precio min: {formatCOP(Number(analysis.summary.price.min || 0))}</div>
                <div className="lbl">Precio max: {formatCOP(Number(analysis.summary.price.max || 0))}</div>
                <div className="lbl">Precio avg: {formatCOP(Number(analysis.summary.price.avg || 0))}</div>
                <div className="lbl">Precio mediana: {formatCOP(Number(analysis.summary.price.median || 0))}</div>
                <div className="lbl">Rating avg: {analysis.summary.rating.avg ?? ''}</div>
                <div className="lbl">Con descuento: {analysis.summary.discount_count}</div>
              </div>
            </div>
          </div>
        )}
      </div>
      </div>
    </>
  )
}