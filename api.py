from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scraper.mercadolibre import (
    scrape_listing,
    scrape_listing_from_url,
    save_results_to_json,
)


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
    out = {
        "keyword": body.url,
        "count": len(items),
        "items": items,
    }
    if body.persist:
        save_results_to_json(items, body.url, f"data/listado.json")
    return out