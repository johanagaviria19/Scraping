from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scraper.mercadolibre import (
    scrape_listing,
    scrape_listing_from_url,
    save_results_to_json,
)
from main import run_analysis
from main import _mongo_upsert_items, mongo_get_items


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchBody(BaseModel):
    keyword: str
    max_pages: Optional[int] = 5
    per_page_delay: Optional[float] = 1.5
    detail_delay: Optional[float] = 1.0
    persist: Optional[bool] = False


class UrlBody(BaseModel):
    url: str
    max_pages: Optional[int] = 5
    per_page_delay: Optional[float] = 1.5
    detail_delay: Optional[float] = 1.0
    persist: Optional[bool] = False


@app.post("/search")
def search(body: SearchBody):
    items = scrape_listing(
        keyword=body.keyword,
        max_pages=body.max_pages or 5,
        per_page_delay=body.per_page_delay or 1.5,
        detail_delay=body.detail_delay or 1.0,
    )
    try:
        _mongo_upsert_items(items, body.keyword)
    except Exception:
        pass
    out = {
        "keyword": body.keyword,
        "count": len(items),
        "items": items,
    }
    if body.persist:
        save_results_to_json(items, body.keyword, f"data/{body.keyword.replace(' ', '_')}.json")
    return out


@app.post("/from-url")
def from_url(body: UrlBody):
    items = scrape_listing_from_url(
        url=body.url,
        max_pages=body.max_pages or 5,
        per_page_delay=body.per_page_delay or 1.5,
        detail_delay=body.detail_delay or 1.0,
    )
    try:
        _mongo_upsert_items(items, body.url)
    except Exception:
        pass
    out = {
        "keyword": body.url,
        "count": len(items),
        "items": items,
    }
    if body.persist:
        save_results_to_json(items, body.url, f"data/listado.json")
    return out


@app.post("/search_with_analysis")
def search_with_analysis(body: SearchBody):
    items = scrape_listing(
        keyword=body.keyword,
        max_pages=body.max_pages or 5,
        per_page_delay=body.per_page_delay or 1.5,
        detail_delay=body.detail_delay or 1.0,
    )
    try:
        _mongo_upsert_items(items, body.keyword)
    except Exception:
        pass
    analysis = run_analysis(items)
    out = {
        "keyword": body.keyword,
        "count": len(items),
        "items": items,
        "analysis": analysis,
    }
    if body.persist:
        save_results_to_json(items, body.keyword, f"data/{body.keyword.replace(' ', '_')}.json")
    return out


@app.post("/from-url_with_analysis")
def from_url_with_analysis(body: UrlBody):
    items = scrape_listing_from_url(
        url=body.url,
        max_pages=body.max_pages or 5,
        per_page_delay=body.per_page_delay or 1.5,
        detail_delay=body.detail_delay or 1.0,
    )
    try:
        _mongo_upsert_items(items, body.url)
    except Exception:
        pass
    analysis = run_analysis(items)
    out = {
        "keyword": body.url,
        "count": len(items),
        "items": items,
        "analysis": analysis,
    }
    if body.persist:
        save_results_to_json(items, body.url, f"data/listado.json")
    return out


@app.get("/data/{keyword}")
def get_data(keyword: str):
    try:
        items = mongo_get_items(keyword)
    except Exception:
        items = []
    return {"keyword": keyword, "count": len(items), "items": items}


@app.post("/search_cached_with_analysis")
def search_cached_with_analysis(body: SearchBody):
    try:
        cached = mongo_get_items(body.keyword)
    except Exception:
        cached = []
    items = cached if cached else scrape_listing(
        keyword=body.keyword,
        max_pages=body.max_pages or 5,
        per_page_delay=body.per_page_delay or 1.5,
        detail_delay=body.detail_delay or 1.0,
    )
    if not cached:
        try:
            _mongo_upsert_items(items, body.keyword)
        except Exception:
            pass
    analysis = run_analysis(items)
    return {"keyword": body.keyword, "count": len(items), "items": items, "analysis": analysis}


@app.get("/save/{keyword}")
def save_keyword(keyword: str):
    items = scrape_listing(
        keyword=keyword,
        max_pages=1,
        per_page_delay=1.5,
        detail_delay=1.0,
    )
    try:
        _mongo_upsert_items(items, keyword)
    except Exception:
        pass
    path = f"data/{keyword.replace(' ', '_')}.json"
    save_results_to_json(items, keyword, path)
    return {"keyword": keyword, "count": len(items), "path": path}