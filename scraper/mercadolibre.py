import re
import time
import random
import json
import unicodedata
from typing import List, Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup


# Lista de User-Agents para rotación básica
USER_AGENTS = [
    # Chrome (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


def _slugify(text: str) -> str:
    """
    Convierte texto a un slug seguro para URL de Mercado Libre.
    - Elimina acentos
    - Reemplaza espacios por guiones
    - Elimina caracteres no alfanuméricos
    """
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ASCII", "ignore").decode("ASCII")
    ascii_text = ascii_text.strip().lower()
    ascii_text = re.sub(r"\s+", "-", ascii_text)
    ascii_text = re.sub(r"[^a-z0-9\-]", "", ascii_text)
    return ascii_text


def build_search_candidates(keyword: str) -> List[str]:
    slug = _slugify(keyword)
    return [
        f"https://listado.mercadolibre.com.co/{slug}",
        f"https://listado.mercadolibre.com.co/{slug}?sb=all_mercadolibre#D[A:{slug}]",
    ]


def _headers() -> Dict[str, str]:
    """
    Retorna headers seguros con rotación de User-Agent.
    """
    ua = random.choice(USER_AGENTS)
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Connection": "keep-alive",
        "Referer": "https://listado.mercadolibre.com.co/",
    }


def _request(url: str, timeout: int = 20) -> Optional[str]:
    """
    Realiza una petición HTTP con reintentos exponenciales simples.
    """
    delay = 1.0
    for attempt in range(4):
        try:
            resp = requests.get(url, headers=_headers(), timeout=timeout)
            if resp.status_code == 200:
                return resp.text
            # Manejo de límites: backoff si 403/429
            if resp.status_code in (403, 429):
                time.sleep(delay + random.uniform(0, 0.5))
                delay *= 2
                continue
            # Otros códigos: intentar una vez más
        except requests.RequestException:
            time.sleep(delay + random.uniform(0, 0.5))
            delay *= 2
    return None

def _request_with_url(url: str, timeout: int = 20) -> Tuple[Optional[str], Optional[str]]:
    delay = 1.0
    for attempt in range(4):
        try:
            resp = requests.get(url, headers=_headers(), timeout=timeout)
            if resp.status_code == 200:
                return resp.text, resp.url
            if resp.status_code in (403, 429):
                time.sleep(delay + random.uniform(0, 0.5))
                delay *= 2
                continue
        except requests.RequestException:
            time.sleep(delay + random.uniform(0, 0.5))
            delay *= 2
    return None, None


def _request_rendered(url: str, wait_selector: str = "li.ui-search-layout__item", timeout_ms: int = 12000) -> Optional[str]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=random.choice(USER_AGENTS), locale="es-ES")
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded")
            for sel in [
                'button:has-text("Aceptar")',
                'button:has-text("Entendido")',
                'button:has-text("OK")',
                '[data-testid="action:understood-button"]',
            ]:
                try:
                    btn = page.locator(sel)
                    if btn and btn.count() > 0:
                        btn.first.click(timeout=2000)
                except Exception:
                    pass
            try:
                page.wait_for_selector(wait_selector, timeout=timeout_ms)
            except Exception:
                try:
                    page.wait_for_selector('a.poly-component__title', timeout=timeout_ms)
                except Exception:
                    try:
                        page.wait_for_selector('script#__PRELOADED_STATE__', timeout=timeout_ms)
                    except Exception:
                        pass
            for _ in range(5):
                try:
                    page.mouse.wheel(0, 1200)
                    page.wait_for_timeout(400)
                except Exception:
                    break
            html = page.content()
            context.close(); browser.close()
            return html
    except Exception:
        return None


def _render_capture_search(url: str, timeout_ms: int = 15000) -> List[Dict]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return []
    results: List[Dict] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=random.choice(USER_AGENTS), locale="es-ES")
            page = context.new_page()
            def handle_response(resp):
                try:
                    url = resp.url
                    if resp.status == 200:
                        ct = resp.headers.get("content-type", "")
                        if "application/json" in ct or "json" in ct:
                            data = resp.json()
                            arr = None
                            if isinstance(data, dict):
                                if isinstance(data.get('results'), list):
                                    arr = data['results']
                                elif isinstance(data.get('items'), list):
                                    arr = data['items']
                                else:
                                    for k, v in data.items():
                                        if isinstance(v, dict) and isinstance(v.get('results'), list):
                                            arr = v['results']; break
                            if arr:
                                for it in arr:
                                    title = it.get('title') or (it.get('name') if isinstance(it.get('name'), str) else None)
                                    permalink = it.get('permalink') or it.get('url')
                                    price = it.get('price') or (it.get('prices',{}).get('price') if isinstance(it.get('prices'), dict) else None)
                                    image = it.get('thumbnail') or it.get('image')
                                    if title and permalink:
                                        results.append({
                                            'title': title,
                                            'url': permalink,
                                            'image': image,
                                            'price': price,
                                            'discount_price': None,
                                            'rating': None,
                                            'rating_count': None,
                                        })
                except Exception:
                    pass
            page.on("response", handle_response)
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(timeout_ms)
            context.close(); browser.close()
    except Exception:
        return []
    return results

def _render_capture_reviews(url: str, timeout_ms: int = 15000, max_reviews: int = 60) -> List[Dict]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return []
    out: List[Dict] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=random.choice(USER_AGENTS), locale="es-ES")
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded")
            for sel in [
                'button:has-text("Aceptar")',
                'button:has-text("Entendido")',
                'button:has-text("OK")',
                '[data-testid="action:understood-button"]',
            ]:
                try:
                    btn = page.locator(sel)
                    if btn and btn.count() > 0:
                        btn.first.click(timeout=2000)
                except Exception:
                    pass
            for sel in [
                'a:has-text("Opiniones")',
                'a:has-text("Ver todas")',
                'a:has-text("Ver más")',
                'a[href*="#reviews"]',
            ]:
                try:
                    lnk = page.locator(sel)
                    if lnk and lnk.count() > 0:
                        lnk.first.click(timeout=3000)
                        break
                except Exception:
                    pass
            try:
                page.wait_for_selector('div.ui-review, section#reviews', timeout=timeout_ms)
            except Exception:
                pass
            for _ in range(12):
                try:
                    page.mouse.wheel(0, 1200)
                    page.wait_for_timeout(400)
                except Exception:
                    break
            cards = page.locator('div.ui-review')
            n = cards.count()
            for i in range(min(n, max_reviews)):
                try:
                    card = cards.nth(i)
                    title = None
                    try:
                        t = card.locator('.ui-review__title')
                        if t.count() > 0:
                            title = t.first.inner_text().strip()
                    except Exception:
                        pass
                    body = None
                    try:
                        b = card.locator('.ui-review__comment-text, .ui-pdp-review__comment')
                        if b.count() > 0:
                            body = b.first.inner_text().strip()
                    except Exception:
                        pass
                    rate = None
                    try:
                        r = card.locator('.ui-review__rating')
                        if r.count() > 0:
                            txt = r.first.inner_text().strip()
                            m = re.search(r"(\d+)(?:\.|,)?", txt)
                            rate = int(m.group(1)) if m else None
                    except Exception:
                        pass
                    date = None
                    try:
                        d = card.locator('time')
                        if d.count() > 0:
                            date = d.first.get_attribute('datetime')
                    except Exception:
                        pass
                    if body or title:
                        out.append({
                            'title': title,
                            'content': body,
                            'rate': rate,
                            'date': date,
                        })
                except Exception:
                    continue
            context.close(); browser.close()
    except Exception:
        return out
    return out

# storage_state helper removido para volver al estado estable
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=random.choice(USER_AGENTS), locale="es-ES")
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded")
            # Intentar aceptar cookies/banners
            for sel in [
                'button:has-text("Aceptar")',
                'button:has-text("Entendido")',
                'button:has-text("OK")',
                '[data-testid="action:understood-button"]',
            ]:
                try:
                    btn = page.locator(sel)
                    if btn and btn.count() > 0:
                        btn.first.click(timeout=2000)
                except Exception:
                    pass
            # Esperar cualquier indicador de listado
            try:
                page.wait_for_selector(wait_selector, timeout=timeout_ms)
            except Exception:
                try:
                    page.wait_for_selector('a.poly-component__title', timeout=timeout_ms)
                except Exception:
                    try:
                        page.wait_for_selector('script#__PRELOADED_STATE__', timeout=timeout_ms)
                    except Exception:
                        pass
            # Desplazar para hidratar contenido perezoso
            for _ in range(5):
                try:
                    page.mouse.wheel(0, 1200)
                    page.wait_for_timeout(400)
                except Exception:
                    break
            html = page.content()
            context.close()
            browser.close()
            return html
    except Exception:
        return None


def _parse_price_block(node) -> Tuple[Optional[float], Optional[float]]:
    """
    Intenta extraer precio y precio con descuento del bloque de precio del listado.
    Devuelve (precio_actual, precio_descuento) donde uno puede ser None.
    """
    if node is None:
        return None, None

    def _as_float(text: str) -> Optional[float]:
        text = text.replace(".", "").replace(",", ".")
        m = re.search(r"(\d+(?:\.\d+)?)", text)
        return float(m.group(1)) if m else None

    # Precio mostrado
    price_spans = node.select("span.andes-money-amount__fraction")
    decimals = node.select("span.andes-money-amount__cents")
    price = None
    if price_spans:
        frac = price_spans[0].get_text(strip=True)
        cent = decimals[0].get_text(strip=True) if decimals else ""
        price = _as_float(f"{frac}{','+cent if cent else ''}")

    # Precio anterior (si aparece tachado en segundo bloque)
    strike = node.select_one("s.ui-search-price__part")
    discount_price = None
    if strike:
        discount_price = _as_float(strike.get_text(strip=True))

    return price, discount_price


def _extract_listing_items(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    items: List[Dict] = []

    for li in soup.select("li.ui-search-layout__item"):
        link = (
            li.select_one("a.poly-component__title")
            or li.select_one("a.ui-search-link")
            or li.select_one("a.ui-search-item__group__link")
            or li.select_one("a.ui-search-result__content-wrapper-link")
        )
        title_node = (
            li.select_one("a.poly-component__title")
            or li.select_one("h2.ui-search-item__title")
            or li.select_one("h3.poly-component__title-wrapper")
        )
        image_node = (
            li.select_one("img.poly-component__picture")
            or li.select_one("img.ui-search-result-image__element")
            or li.select_one("img")
        )
        price_block = li
        title = None
        if title_node:
            if title_node.name == "a":
                title = title_node.get_text(strip=True)
            else:
                title = title_node.get_text(strip=True)
        url = link["href"] if link and link.has_attr("href") else None
        image = image_node["data-src"] if image_node and image_node.has_attr("data-src") else (
            image_node["src"] if image_node and image_node.has_attr("src") else None
        )
        price, discount_price = _parse_price_block(price_block)
        rating_avg = None
        rating_count = None
        rating_node = (
            li.select_one("span.ui-search-reviews__rating-number")
            or li.select_one("span.ui-search-reviews__rating")
        )
        if rating_node:
            try:
                rating_avg = float(rating_node.get_text(strip=True).replace(",", "."))
            except Exception:
                rating_avg = None
        count_node = li.select_one("span.ui-search-reviews__amount")
        if count_node:
            m = re.search(r"(\d+)", count_node.get_text(strip=True))
            rating_count = int(m.group(1)) if m else None
        items.append({
            "title": title,
            "url": url,
            "image": image,
            "price": price,
            "discount_price": discount_price,
            "rating": rating_avg,
            "rating_count": rating_count,
        })

    if items:
        return items

    for div in soup.select("div.ui-search-result, div.ui-search-result__wrapper"):
        link = (
            div.select_one("a.poly-component__title")
            or div.select_one("a.ui-search-link")
            or div.select_one("a.ui-search-item__group__link")
            or div.select_one("a.ui-search-result__content-wrapper-link")
        )
        title_node = (
            div.select_one("a.poly-component__title")
            or div.select_one("h2.ui-search-item__title")
            or div.select_one("h3.poly-component__title-wrapper")
        )
        image_node = (
            div.select_one("img.poly-component__picture")
            or div.select_one("img.ui-search-result-image__element")
            or div.select_one("img")
        )
        price_block = div
        title = None
        if title_node:
            if title_node.name == "a":
                title = title_node.get_text(strip=True)
            else:
                title = title_node.get_text(strip=True)
        url = link["href"] if link and link.has_attr("href") else None
        image = image_node["data-src"] if image_node and image_node.has_attr("data-src") else (
            image_node["src"] if image_node and image_node.has_attr("src") else None
        )
        price, discount_price = _parse_price_block(price_block)
        items.append({
            "title": title,
            "url": url,
            "image": image,
            "price": price,
            "discount_price": discount_price,
            "rating": None,
            "rating_count": None,
        })

    if items:
        return items

    try:
        script = soup.select_one('script#__PRELOADED_STATE__')
        if script and script.text:
            state = json.loads(script.text)
            search = None
            if isinstance(state, dict):
                search = state.get('pageStoreState', {}).get('search')
                if not search:
                    search = state.get('pageState', {}).get('initialState')
            results = search.get('results', []) if isinstance(search, dict) else []
            for it in results:
                try:
                    t = it.get('title')
                    title = t.get('text') if isinstance(t, dict) else t
                    url = it.get('permalink')
                    price = it.get('price')
                    image = it.get('thumbnail') or it.get('image')
                    rv = it.get('reviews') or {}
                    rating_avg = rv.get('rating_average')
                    rating_count = rv.get('total')
                    if url and title:
                        items.append({
                            'title': title,
                            'url': url,
                            'image': image,
                            'price': price,
                            'discount_price': None,
                            'rating': rating_avg,
                            'rating_count': rating_count,
                        })
                except Exception:
                    continue
    except Exception:
        pass

    if items:
        return items

    try:
        for ld in soup.select('script[type="application/ld+json"]'):
            data = json.loads(ld.string or ld.text or '{}')
            if isinstance(data, dict) and data.get('@type') in ('ItemList', 'SearchResultsPage'):
                elements = data.get('itemListElement') or []
                for el in elements:
                    try:
                        item = el.get('item') if isinstance(el.get('item'), dict) else el
                        name = item.get('name') or el.get('name')
                        url = item.get('url') or el.get('url')
                        offers = item.get('offers') or {}
                        price = None
                        if isinstance(offers, dict):
                            price = offers.get('price') or offers.get('priceSpecification', {}).get('price')
                        agg = item.get('aggregateRating') or {}
                        rating = agg.get('ratingValue')
                        count = agg.get('reviewCount')
                        if url and name:
                            items.append({
                                'title': name,
                                'url': url,
                                'image': None,
                                'price': price,
                                'discount_price': None,
                                'rating': rating,
                                'rating_count': count,
                            })
                    except Exception:
                        continue
    except Exception:
        pass

    return items


def _parse_query_from_listado_url(url: str) -> Optional[str]:
    m = re.search(r"listado\.mercadolibre\.com\.co/([^\/?#]+)", url)
    if m:
        slug = m.group(1)
        slug = slug.replace('-', ' ')
        return slug
    m2 = re.search(r"#D\[A:([^\]]+)\]", url)
    if m2:
        slug = m2.group(1)
        slug = slug.replace('-', ' ')
        return slug
    return None


def _api_search_items(query: str, limit: int = 50) -> List[Dict]:
    url = f"https://api.mercadolibre.com/sites/MCO/search?q={requests.utils.quote(query)}&limit={limit}"
    try:
        hdrs = _headers()
        hdrs["Accept"] = "application/json"
        hdrs["Origin"] = "https://listado.mercadolibre.com.co"
        resp = requests.get(url, headers=hdrs, timeout=20)
        if resp.status_code != 200:
            return []
        data = resp.json()
        results = data.get('results', [])
        items: List[Dict] = []
        for it in results:
            title = it.get('title')
            permalink = it.get('permalink')
            price = it.get('price')
            image = it.get('thumbnail')
            if title and permalink:
                items.append({
                    'title': title,
                    'url': permalink,
                    'image': image,
                    'price': price,
                    'discount_price': None,
                    'rating': None,
                    'rating_count': None,
                })
        return items
    except Exception:
        return []

def _is_product_url(u: Optional[str]) -> bool:
    if not u:
        return False
    return bool(re.search(r"(articulo\.mercadolibre\.com\.co|www\.mercadolibre\.com\.co/.*/p/)", u))


def _find_next_page(html: str) -> Optional[str]:
    """
    Encuentra el enlace a la siguiente página del listado.
    """
    soup = BeautifulSoup(html, "lxml")
    next_btn = soup.select_one("li.andes-pagination__button--next a")
    if next_btn and next_btn.has_attr("href"):
        return next_btn["href"]
    return None


def _extract_product_detail(html: str, base_url: Optional[str] = None) -> Dict:
    """
    Extrae información del detalle del producto: descripción, vendidos, calificación.
    """
    soup = BeautifulSoup(html, "lxml")

    # Descripción
    description = None
    desc_node = soup.select_one("div.ui-pdp-description__content") or soup.select_one("p.ui-pdp-description__content")
    if desc_node:
        description = desc_node.get_text("\n", strip=True)
    else:
        desc_node_legacy = soup.select_one("div.item-description")
        if desc_node_legacy:
            description = desc_node_legacy.get_text("\n", strip=True)

    # Vendidos
    sold = None
    sold_text = None
    sold_node = soup.select_one("span.ui-pdp-subtitle")
    if sold_node:
        sold_text = sold_node.get_text(strip=True)
        mm = re.search(r"(\d+)", sold_text)
        if mm:
            try:
                sold = int(mm.group(1))
            except Exception:
                sold = None

    # Calificación promedio y cantidad
    rating = None
    rating_count = None
    # Meta schema
    rating_val = soup.select_one('[itemprop="ratingValue"]')
    if rating_val and rating_val.has_attr("content"):
        try:
            rating = float(rating_val["content"])
        except Exception:
            pass
    rating_cnt = soup.select_one('[itemprop="ratingCount"]')
    if rating_cnt and rating_cnt.has_attr("content"):
        try:
            rating_count = int(rating_cnt["content"])
        except Exception:
            pass

    # Fallback
    if rating is None:
        rnode = soup.select_one("span.ui-pdp-review__rating")
        if rnode:
            try:
                rating = float(rnode.get_text(strip=True).replace(",", "."))
            except Exception:
                pass

    if rating_count is None:
        cnode = soup.select_one("span.ui-pdp-review__amount")
        if cnode:
            mm = re.search(r"(\d+)", cnode.get_text(strip=True))
            rating_count = int(mm.group(1)) if mm else None

    reviews: List[Dict] = []
    for r in soup.select("div.ui-review"):
        try:
            title = None
            tnode = r.select_one(".ui-review__title")
            if tnode:
                title = tnode.get_text(strip=True)
            body = None
            bnode = r.select_one(".ui-review__comment-text") or r.select_one(".ui-pdp-review__comment")
            if bnode:
                body = bnode.get_text("\n", strip=True)
            rate = None
            rnode = r.select_one(".ui-review__rating")
            if rnode:
                m = re.search(r"(\d+)(?:\.|,)?", rnode.get_text(strip=True))
                rate = int(m.group(1)) if m else None
            date = None
            dnode = r.select_one("time")
            if dnode and dnode.has_attr("datetime"):
                date = dnode["datetime"]
            if body or title:
                reviews.append({
                    "title": title,
                    "content": body,
                    "rate": rate,
                    "date": date,
                })
        except Exception:
            continue
    if not reviews:
        try:
            for ld in soup.select('script[type="application/ld+json"]'):
                data = json.loads(ld.string or ld.text or '{}')
                if isinstance(data, dict):
                    rlist = data.get("review")
                    if isinstance(rlist, list):
                        for rv in rlist:
                            try:
                                title = rv.get("name")
                                body = rv.get("reviewBody")
                                rate = None
                                rt = rv.get("reviewRating") or {}
                                if isinstance(rt, dict):
                                    rate = int(rt.get("ratingValue") or 0) or None
                                date = rv.get("datePublished")
                                if body or title:
                                    reviews.append({
                                        "title": title,
                                        "content": body,
                                        "rate": rate,
                                        "date": date,
                                    })
                            except Exception:
                                continue
        except Exception:
            pass
    if base_url and len(reviews) < 10:
        try:
            more = _render_capture_reviews(base_url, timeout_ms=15000, max_reviews=60)
            if more:
                reviews.extend(more)
        except Exception:
            pass
    return {
        "description": description,
        "sold": sold,
        "detail_rating": rating,
        "detail_rating_count": rating_count,
        "reviews": reviews[:60],
    }


def scrape_listing(keyword: str, max_pages: int = 10, per_page_delay: float = 1.5, detail_delay: float = 1.0) -> List[Dict]:
    """
    Recorre el listado de Mercado Libre para la palabra clave y devuelve
    una lista de dicts con la información de productos. Visita cada detalle
    para enriquecer con descripción y métricas adicionales.
    """
    candidates = build_search_candidates(keyword)
    url = None
    html = None
    for cand in candidates:
        html_try = _request(cand)
        parsed = _extract_listing_items(html_try or "") if html_try else []
        if not parsed:
            html_try2 = _request_rendered(cand)
            parsed = _extract_listing_items(html_try2 or "") if html_try2 else []
            if parsed:
                html_try = html_try2
        if any(it.get("title") for it in parsed):
            url = cand
            html = html_try
            break
    if url is None:
        if candidates:
            url_flow_items = scrape_listing_from_url(
                candidates[-1],
                max_pages=max_pages,
                per_page_delay=per_page_delay,
                detail_delay=detail_delay,
            )
            if url_flow_items:
                return url_flow_items
        api_items = _api_search_items(keyword)
        if api_items:
            return api_items
        render_items = _render_capture_search(candidates[0]) if candidates else []
        if render_items:
            return render_items
        return []
    all_items: List[Dict] = []
    seen_urls = set()

    pages_scraped = 0
    next_url = url
    while next_url and pages_scraped < max_pages:
        if pages_scraped > 0:
            html = _request(next_url)
            if not html:
                break

        listing_items = _extract_listing_items(html)
        if not listing_items and pages_scraped == 0:
            html2 = _request_rendered(next_url)
            if html2:
                listing_items = _extract_listing_items(html2)
                html = html2
        for item in listing_items:
            # Enriquecer con detalle si hay URL
            if item.get("url"):
                time.sleep(detail_delay + random.uniform(0, 0.5))
                detail_html, final_url = _request_with_url(item["url"])
                if detail_html:
                    detail = _extract_product_detail(detail_html, final_url or item.get("url"))
                    item.update(detail)
                    if final_url:
                        item["url"] = final_url

            # Normalizar rating/amount (preferir detalle si existe)
            item["rating"] = item.get("detail_rating") or item.get("rating")
            item["rating_count"] = item.get("detail_rating_count") or item.get("rating_count")
            item.pop("detail_rating", None)
            item.pop("detail_rating_count", None)

            if _is_product_url(item.get("url")) and item.get("title"):
                if item["url"] in seen_urls:
                    continue
                seen_urls.add(item["url"])
                all_items.append(item)

        pages_scraped += 1
        next_url = _find_next_page(html)

        if next_url:
            time.sleep(per_page_delay + random.uniform(0, 0.5))

    return all_items


def save_results_to_json(results: List[Dict], keyword: str, out_path: str) -> str:
    """
    Guarda resultados en un archivo JSON y devuelve la ruta escrita.
    """
    data = {
        "keyword": keyword,
        "count": len(results),
        "items": results,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return out_path


def scrape_listing_from_url(url: str, max_pages: int = 10, per_page_delay: float = 1.5, detail_delay: float = 1.0) -> List[Dict]:
    q_direct = _parse_query_from_listado_url(url)
    if q_direct:
        items_direct = scrape_listing(q_direct, max_pages=max_pages, per_page_delay=per_page_delay, detail_delay=detail_delay)
        if items_direct:
            return items_direct
    html = _request(url)
    if not html:
        html = _request_rendered(url)
        if not html:
            return []
    prim_items = _extract_listing_items(html)
    if not prim_items:
        q0 = _parse_query_from_listado_url(url)
        if q0:
            alt_items = scrape_listing(q0, max_pages=max_pages, per_page_delay=per_page_delay, detail_delay=detail_delay)
            if alt_items:
                return alt_items
    all_items: List[Dict] = []
    seen_urls = set()
    pages_scraped = 0
    next_url = url
    while next_url and pages_scraped < max_pages:
        if pages_scraped > 0:
            html = _request(next_url)
            if not html:
                html = _request_rendered(next_url)
                if not html:
                    break
        listing_items = _extract_listing_items(html)
        if not listing_items and pages_scraped == 0:
            html2 = _request_rendered(next_url)
            if html2:
                listing_items = _extract_listing_items(html2)
                html = html2
        # Si no hay resultados, intenta canonicalizar con el slug y usar candidatos SSR
        if not listing_items and pages_scraped == 0:
            q = _parse_query_from_listado_url(next_url)
            if q:
                for cand in build_search_candidates(q):
                    html_try = _request(cand) or _request_rendered(cand)
                    if not html_try:
                        continue
                    parsed = _extract_listing_items(html_try)
                    if parsed:
                        next_url = cand
                        html = html_try
                        listing_items = parsed
                        break
                if not listing_items:
                    # Fallback final: usar flujo por palabra clave completo
                    return scrape_listing(q, max_pages=max_pages, per_page_delay=per_page_delay, detail_delay=detail_delay)
        if not listing_items:
            q = _parse_query_from_listado_url(next_url)
            if q:
                listing_items = _api_search_items(q)
        if not listing_items:
            listing_items = _render_capture_search(next_url)
        for item in listing_items:
            if item.get("url"):
                time.sleep(detail_delay + random.uniform(0, 0.5))
                detail_html, final_url = _request_with_url(item["url"])
                if detail_html:
                    detail = _extract_product_detail(detail_html, final_url or item.get("url"))
                    item.update(detail)
                    if final_url:
                        item["url"] = final_url
            item["rating"] = item.get("detail_rating") or item.get("rating")
            item["rating_count"] = item.get("detail_rating_count") or item.get("rating_count")
            item.pop("detail_rating", None)
            item.pop("detail_rating_count", None)
            if _is_product_url(item.get("url")) and item.get("title"):
                if item["url"] in seen_urls:
                    continue
                seen_urls.add(item["url"])
                all_items.append(item)
        pages_scraped += 1
        next_url = _find_next_page(html)
        if next_url:
            time.sleep(per_page_delay + random.uniform(0, 0.5))
    return all_items