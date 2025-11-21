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
}

type ApiResponse = {
  keyword: string
  count: number
  items: Item[]
}

const API_BASE = 'http://localhost:8000'

export default function App() {
  const [source, setSource] = useState('telefono')
  const [isUrl, setIsUrl] = useState(false)
  const [maxPages, setMaxPages] = useState(5)
  const [perPageDelay, setPerPageDelay] = useState(1.5)
  const [detailDelay, setDetailDelay] = useState(1.0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<ApiResponse | null>(null)

  const canSearch = useMemo(() => source.trim().length > 0, [source])

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
      setData(json)
    } catch (e: any) {
      setError(String(e?.message || e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>Comparador Mercado Libre</h1>
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
                  <td>{it.rating_count ?? ''}</td>
                  <td>{it.sold ?? ''}</td>
                  <td>{it.url ? <a href={it.url} target="_blank" rel="noreferrer">Abrir</a> : ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}