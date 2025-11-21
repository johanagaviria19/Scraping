import { useMemo, useState } from 'react'

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

export default function App() {
  const [source, setSource] = useState('telefono')
  const [isUrl, setIsUrl] = useState(false)
  const [maxPages, setMaxPages] = useState(5)
  const [perPageDelay, setPerPageDelay] = useState(1.5)
  const [detailDelay, setDetailDelay] = useState(1.0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<ApiResponse | null>(null)
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [username, setUsername] = useState('user')
  const [password, setPassword] = useState('pass')
  const [token, setToken] = useState<string | null>(null)

  const canSearch = useMemo(() => source.trim().length > 0, [source])

  const ratingColor = (r?: number | null) => {
    const v = Number(r || 0)
    if (v >= 4.5) return '#2ecc71'
    if (v >= 3.5) return '#f1c40f'
    return '#e74c3c'
  }

  const barWidth = (r?: number | null, max = 400) => `${Math.max(2, Math.min(max, (Number(r || 0) / 5) * max))}px`

  const runSearch = async () => {
    if (!canSearch) return
    setLoading(true)
    setError(null)
    try {
      const endpoint = isUrl ? '/from-url_with_analysis' : '/search_cached_with_analysis'
      const body = isUrl
        ? { url: source, max_pages: maxPages, per_page_delay: perPageDelay, detail_delay: detailDelay }
        : { keyword: source, max_pages: maxPages, per_page_delay: perPageDelay, detail_delay: detailDelay }
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

  const register = async () => {
    setError(null)
    const res = await fetch(`${JAVA_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!res.ok && res.status !== 201) setError(`HTTP ${res.status}`)
  }

  const login = async () => {
    setError(null)
    const res = await fetch(`${JAVA_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!res.ok) { setError(`HTTP ${res.status}`); return }
    const json = await res.json()
    setToken(json?.accessToken || null)
  }

  return (
    <div className="container">
      <h1>Comparador Mercado Libre</h1>
      <div className="card">
        <div className="row">
          <input className="input" placeholder="Usuario" value={username} onChange={(e) => setUsername(e.target.value)} />
          <input className="input" placeholder="Contraseña" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <button className="btn" onClick={register}>Registrar</button>
          <button className="btn" onClick={login}>{token ? 'Sesión abierta' : 'Login'}</button>
        </div>
      </div>
      <div className="card">
        <div className="row">
          <label>
            <input type="checkbox" checked={isUrl} onChange={(e) => setIsUrl(e.target.checked)} />
            Usar URL de listado
          </label>
        </div>
        <div className="row">
          <input
            value={source}
            onChange={(e) => setSource(e.target.value)}
            placeholder={isUrl ? 'https://listado.mercadolibre.com.co/...' : 'Palabra clave'}
            className="input"
          />
          <button className="btn" onClick={runSearch} disabled={!canSearch || loading}>
            {loading ? 'Buscando...' : 'Buscar'}
          </button>
        </div>
        <div className="row">
          <label className="lbl">Máx. páginas</label>
          <input type="number" min={1} max={20} value={maxPages} onChange={(e) => setMaxPages(Number(e.target.value))} />
          <label className="lbl">Delay por página (s)</label>
          <input type="number" step={0.5} min={0} value={perPageDelay} onChange={(e) => setPerPageDelay(Number(e.target.value))} />
          <label className="lbl">Delay por detalle (s)</label>
          <input type="number" step={0.5} min={0} value={detailDelay} onChange={(e) => setDetailDelay(Number(e.target.value))} />
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {data && (
        <div className="results">
          <h2>
            Resultados ({data.count})
          </h2>
          <table>
            <thead>
              <tr>
                <th>Producto</th>
                <th>Precio</th>
                <th>Descuento</th>
                <th>Rating</th>
                <th>Opiniones</th>
                <th>Vendidos</th>
                <th>Enlace</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((it, idx) => (
                <tr key={idx}>
                  <td className="title">
                    {it.image ? <img src={it.image} alt="" /> : null}
                    <span>{it.title}</span>
                  </td>
                  <td>{it.price ?? ''}</td>
                  <td>{it.discount_price ?? ''}</td>
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
          <h2>Análisis</h2>
          <div className="card">
            <div className="row">
              <div className="lbl">Items: {analysis.summary.count}</div>
              <div className="lbl">Precio min: {analysis.summary.price.min ?? ''}</div>
              <div className="lbl">Precio max: {analysis.summary.price.max ?? ''}</div>
              <div className="lbl">Precio avg: {analysis.summary.price.avg ?? ''}</div>
              <div className="lbl">Precio mediana: {analysis.summary.price.median ?? ''}</div>
              <div className="lbl">Rating avg: {analysis.summary.rating.avg ?? ''}</div>
              <div className="lbl">Con descuento: {analysis.summary.discount_count}</div>
            </div>
          </div>

          <div className="card">
            <h3>Distribución de precios</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {(() => {
                const buckets = analysis.histogram_price
                const max = Math.max(1, ...buckets.map(b => b.count))
                return buckets.map((b, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 160 }}>{Math.round(b.min)} - {Math.round(b.max)}</div>
                    <div style={{ background: '#4a90e2', height: 16, width: `${(b.count / max) * 400}px` }} />
                    <div>{b.count}</div>
                  </div>
                ))
              })()}
            </div>
          </div>

          

          <div className="card">
            <h3>Sentimiento de reseñas</h3>
            <div className="row">
              <div className="lbl">Reseñas: {analysis.sentiment.count}</div>
              <div className="lbl">Positivas: {analysis.sentiment.positive ?? ''}</div>
              <div className="lbl">Negativas: {analysis.sentiment.negative ?? ''}</div>
              <div className="lbl">Neutras: {analysis.sentiment.neutral ?? ''}</div>
              <div className="lbl">Score promedio: {analysis.sentiment.avg_score ?? ''}</div>
            </div>
          </div>
          {analysis.reviews_report && (
            <>
              <div className="card">
                <h3>Ranking de productos</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {analysis.reviews_report.ranking.slice(0, 10).map((p, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ width: 28 }}>{idx + 1}</div>
                      <div style={{ width: 320, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.title}</div>
                      <div style={{ background: ratingColor(p.avg_rating), height: 16, width: barWidth(p.avg_rating) }} />
                      <div style={{ width: 60 }}>{p.avg_rating.toFixed(2)}</div>
                      <div style={{ width: 100 }}>Reseñas: {p.reviews_count}</div>
                      <div style={{ width: 120 }}>4-5★: {(p.positive_pct * 100).toFixed(0)}%</div>
                      {p.url ? <a href={p.url || ''} target="_blank" rel="noreferrer">Abrir</a> : null}
                    </div>
                  ))}
                </div>
              </div>

              <div className="card">
                <h3>Top 3 productos</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {analysis.reviews_report.top3.map((p, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ width: 28 }}>{idx + 1}</div>
                      <div style={{ width: 320, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.title}</div>
                      <div style={{ background: ratingColor(p.avg_rating), height: 16, width: barWidth(p.avg_rating) }} />
                      <div style={{ width: 60 }}>{p.avg_rating.toFixed(2)}</div>
                      <div style={{ width: 100 }}>Reseñas: {p.reviews_count}</div>
                      <div style={{ width: 120 }}>4-5★: {(p.positive_pct * 100).toFixed(0)}%</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card">
                <h3>Producto estrella</h3>
                {analysis.reviews_report.star_product ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{ fontSize: 22 }}>⭐</div>
                    <div style={{ width: 320, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{analysis.reviews_report.star_product.title}</div>
                    <div style={{ background: ratingColor(analysis.reviews_report.star_product.avg_rating), height: 16, width: barWidth(analysis.reviews_report.star_product.avg_rating) }} />
                    <div style={{ width: 60 }}>{analysis.reviews_report.star_product.avg_rating.toFixed(2)}</div>
                    <div style={{ width: 100 }}>Reseñas: {analysis.reviews_report.star_product.reviews_count}</div>
                    <div style={{ width: 120 }}>4-5★: {(analysis.reviews_report.star_product.positive_pct * 100).toFixed(0)}%</div>
                  </div>
                ) : (
                  <div className="lbl">Sin producto que cumpla mínimo de 20 reseñas</div>
                )}
              </div>

              <div className="card">
                <h3>Reseñas destacadas</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {analysis.reviews_report.best_reviews_by_product.map((pr, idx) => (
                    <div key={idx}>
                      <div style={{ fontWeight: 600, marginBottom: 6 }}>{pr.title}</div>
                      {pr.reviews.length > 0 ? pr.reviews.map((rv, j) => (
                        <div key={j} style={{ display: 'flex', flexDirection: 'row', gap: 10, alignItems: 'flex-start' }}>
                          <div style={{ width: 80 }}>⭐ {rv.rate}</div>
                          <div style={{ width: 140 }}>{rv.date ?? ''}</div>
                          <div style={{ flex: 1 }}>{rv.content}</div>
                        </div>
                      )) : <div className="lbl">Sin reseñas que cumplan criterios</div>}
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}