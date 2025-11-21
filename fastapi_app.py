import os
import logging
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from scraper.mercadolibre import scrape_listing, scrape_listing_from_url, send_results_to_java

logging.basicConfig(level=logging.DEBUG)

app = FastAPI()


class ProcessRequest(BaseModel):
    keyword: Optional[str] = None
    url: Optional[str] = None
    max_pages: int = 5
    per_page_delay: float = 1.5
    detail_delay: float = 1.0


def _java_cfg():
    return os.environ.get("JAVA_API_URL", "http://localhost:8080"), os.environ.get("PYTHON_SERVICE_TOKEN")


@app.post("/process")
def process(req: ProcessRequest):
    if req.url:
        items = scrape_listing_from_url(req.url, max_pages=req.max_pages, per_page_delay=req.per_page_delay, detail_delay=req.detail_delay)
        source = req.url
    else:
        items = scrape_listing(req.keyword or "", max_pages=req.max_pages, per_page_delay=req.per_page_delay, detail_delay=req.detail_delay)
        source = req.keyword or ""
    java_url, token = _java_cfg()
    ok = send_results_to_java(items, source, java_url, token)
    logging.info("process ok=%s count=%s", ok, len(items))
    return {"ok": ok, "count": len(items)}


@app.get("/health")
def health():
    return {"status": "ok"}