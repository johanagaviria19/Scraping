"use client"
import { useEffect, useMemo, useState } from "react"

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

const API_BASE = 'http://localhost:8000'
const JAVA_BASE = 'http://localhost:8080'

export default function Home() {
  const [token, setToken] = useState<string | null>(null)
  const [source, setSource] = useState('telefono')
  const [isUrl, setIsUrl] = useState(false)
  const [maxPages, setMaxPages] = useState(5)
  const [perPageDelay, setPerPageDelay] = useState(1.5)
  const [detailDelay, setDetailDelay] = useState(1.0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<ApiResponse | null>(null)
  const [priceMin, setPriceMin] = useState(0)
  const [priceMax, setPriceMax] = useState(0)
  const [priceValMin, setPriceValMin] = useState(0)
  const [priceValMax, setPriceValMax] = useState(0)
  const [ratingMin, setRatingMin] = useState(0)
  const [ratingMax, setRatingMax] = useState(5)
  const [ratingValMin, setRatingValMin] = useState(0)
  const [ratingValMax, setRatingValMax] = useState(5)
  const [onlyDiscount, setOnlyDiscount] = useState(false)

  const canSearch = useMemo(() => source.trim().length > 0, [source])

  const fmt = (v: any) => {
    if (v === null || v === undefined) return ''
    const n = Number(v)
    if (Number.isNaN(n)) return ''
    return n.toLocaleString('es-CO')
  }

  const cop = (v: any) => {
    if (v === null || v === undefined) return ''
    const n = Number(v)
    if (Number.isNaN(n)) return ''
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n)
  }

  useEffect(() => {
    const t = localStorage.getItem('auth_token')
    if (!t) {
      location.href = '/login'
      return
    }
    setToken(t)
  }, [])

  useEffect(() => {
    const prices = (data?.items || []).map(i => Number(i.price)).filter(n => !Number.isNaN(n) && n > 0)
    if (prices.length) {
      const pmin = Math.min(...prices)
      const pmax = Math.max(...prices)
      setPriceMin(pmin)
      setPriceMax(pmax)
      setPriceValMin(pmin)
      setPriceValMax(pmax)
    }
    const ratings = (data?.items || []).map(i => Number(i.rating)).filter(n => !Number.isNaN(n) && n >= 0)
    if (ratings.length) {
      const rmin = Math.max(0, Math.min(...ratings))
      const rmax = Math.min(5, Math.max(...ratings))
      setRatingMin(rmin)
      setRatingMax(Math.max(rmin + 1, rmax))
      setRatingValMin(rmin)
      setRatingValMax(Math.max(rmin + 1, rmax))
    }
  }, [data])

  const filtered = useMemo(() => {
    let items = (data?.items || []).slice()
    items = items.filter(i => {
      const p = Number(i.price)
      const r = Number(i.rating || 0)
      const okP = Number.isNaN(p) ? true : (p >= priceValMin && p <= priceValMax)
      const okR = r >= ratingValMin && r <= ratingValMax
      const okD = !onlyDiscount || (i.discount_price != null)
      return okP && okR && okD
    })
    return items
  }, [data, priceValMin, priceValMax, ratingValMin, ratingValMax, onlyDiscount])

  const runSearch = async () => {
    if (!canSearch) return
    setLoading(true)
    setError(null)
    try {
      const endpoint = isUrl ? '/from-url' : '/search'
      const body = isUrl
        ? { url: source, max_pages: maxPages, per_page_delay: perPageDelay, detail_delay: detailDelay }
        : { keyword: source, max_pages: maxPages, per_page_delay: perPageDelay, detail_delay: detailDelay }
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = (await res.json()) as ApiResponse
      try {
        await fetch(`${JAVA_BASE}/api/data`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(json),
        })
      } catch {}
      setData(json)
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

  const logout = () => {
    localStorage.removeItem('auth_token')
    location.href = '/login'
  }

  if (!token) return null

  return (
    <div className="page">
      <aside className="sidebar">
        <h3>Búsqueda</h3>
        <div className="stack">
          <label className="lbl"><input type="checkbox" checked={isUrl} onChange={(e) => setIsUrl(e.target.checked)} /> Usar URL</label>
          <input className="input" value={source} onChange={(e) => setSource(e.target.value)} placeholder={isUrl ? 'https://listado.mercadolibre.com.co/...' : 'Palabra clave'} />
          <label className="lbl">Máx. páginas</label>
          <input type="range" min={1} max={20} value={maxPages} onChange={(e) => setMaxPages(Number(e.target.value))} />
          <div className="hint">{maxPages}</div>
          <label className="lbl">Delay por página (s)</label>
          <input type="range" min={0} max={5} step={0.5} value={perPageDelay} onChange={(e) => setPerPageDelay(Number(e.target.value))} />
          <div className="hint">{perPageDelay.toFixed(2)}</div>
          <label className="lbl">Delay por detalle (s)</label>
          <input type="range" min={0} max={5} step={0.5} value={detailDelay} onChange={(e) => setDetailDelay(Number(e.target.value))} />
          <div className="hint">{detailDelay.toFixed(2)}</div>
          <div className="row">
            <button className="btn wide" onClick={runSearch} disabled={!canSearch || loading}>{loading ? 'Buscando...' : 'Buscar y actualizar datos'}</button>
          </div>
        </div>
      </aside>
      <main className="main">
        <div className="topbar">
          <h1>Dashboard comparativo de Mercado Libre</h1>
          <button className="btn" onClick={logout}>Cerrar sesión</button>
        </div>
        {error && <div className="error">{error}</div>}

        {data && (
          <>
            <div className="filters">
              <div className="filter">
                <div className="lbl">Rango de precio</div>
                <input type="range" min={priceMin} max={priceMax} step={1000} value={priceValMin} onChange={(e) => setPriceValMin(Number(e.target.value))} />
                <input type="range" min={priceMin} max={priceMax} step={1000} value={priceValMax} onChange={(e) => setPriceValMax(Number(e.target.value))} />
                <div className="range"><span>{cop(priceValMin)}</span><span>{cop(priceValMax)}</span></div>
              </div>
              <div className="filter">
                <div className="lbl">Rango de calificación</div>
                <input type="range" min={ratingMin} max={ratingMax} step={0.1} value={ratingValMin} onChange={(e) => setRatingValMin(Number(e.target.value))} />
                <input type="range" min={ratingMin} max={ratingMax} step={0.1} value={ratingValMax} onChange={(e) => setRatingValMax(Number(e.target.value))} />
                <div className="range"><span>{ratingValMin.toFixed(2)}</span><span>{ratingValMax.toFixed(2)}</span></div>
              </div>
              <label className="lbl"><input type="checkbox" checked={onlyDiscount} onChange={(e) => setOnlyDiscount(e.target.checked)} /> Solo productos con descuento</label>
            </div>

            <div className="card">
              <h2>Tabla de productos</h2>
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
              {filtered.map((it, idx) => (
                <tr key={idx}>
                  <td className="title">
                    {it.image ? <img src={it.image} alt="" /> : null}
                    <span>{it.title}</span>
                  </td>
                <td className="num">{cop(it.price)}</td>
                <td className="num">{cop(it.discount_price)}</td>
                <td className="num" title={it.rating != null ? `${Number(it.rating).toFixed(1)} / 5` : ''}>
                  {it.rating != null ? `${Number(it.rating).toFixed(1)} ★` : ''}
                </td>
                <td className="num" title={(() => { const v = it.rating_count ?? (it.reviews ? it.reviews.length : undefined); return v != null ? `${v} opiniones` : ''; })()}>
                  {(() => {
                    const v = it.rating_count ?? (it.reviews ? it.reviews.length : undefined)
                    if (v == null) return ''
                    const hot = Number(v) >= 100
                    return <span className={hot ? 'badge badge-hot' : 'badge'}>{fmt(v)}</span>
                  })()}
                </td>
                <td className="num" title={it.sold != null ? `${it.sold} vendidos` : ''}>{fmt(it.sold)}</td>
                <td>{it.url ? <a href={it.url} target="_blank" rel="noreferrer">Abrir</a> : ''}</td>
              </tr>
            ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
