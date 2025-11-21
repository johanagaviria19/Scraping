import argparse
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from pymongo import MongoClient, UpdateOne
import hashlib
import json

from scraper.mercadolibre import scrape_listing, scrape_listing_from_url, save_results_to_json, send_results_to_java

def to_dataframe(items: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(items)
    expected = [
        "title",
        "price",
        "discount_price",
        "rating",
        "rating_count",
        "sold",
        "url",
        "image",
        "description",
    ]
    for col in expected:
        if col not in df.columns:
            df[col] = pd.NA
    for col in ["price", "discount_price", "rating", "rating_count", "sold"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["has_discount"] = df["discount_price"].notna()
    price = df["price"].copy()
    price = price.where(price > 0)
    df["benefit"] = (df["rating"].fillna(0)) / price
    return df

def _histogram(series: pd.Series, bins: int = 30) -> List[Dict[str, Any]]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return []
    cat = pd.cut(s, bins=bins, include_lowest=True)
    intervals = list(cat.cat.categories)
    counts = list(cat.value_counts(sort=False))
    out: List[Dict[str, Any]] = []
    for i, iv in enumerate(intervals):
        out.append({
            "min": float(getattr(iv, "left", None) or 0.0),
            "max": float(getattr(iv, "right", None) or 0.0),
            "count": int(counts[i]),
        })
    return out

def _summary(df: pd.DataFrame) -> Dict[str, Any]:
    price = pd.to_numeric(df["price"], errors="coerce")
    rating = pd.to_numeric(df["rating"], errors="coerce")
    return {
        "count": int(len(df)),
        "price": {
            "min": float(price.dropna().min()) if price.dropna().size else None,
            "max": float(price.dropna().max()) if price.dropna().size else None,
            "avg": float(price.dropna().mean()) if price.dropna().size else None,
            "median": float(price.dropna().median()) if price.dropna().size else None,
        },
        "rating": {
            "min": float(rating.dropna().min()) if rating.dropna().size else None,
            "max": float(rating.dropna().max()) if rating.dropna().size else None,
            "avg": float(rating.dropna().mean()) if rating.dropna().size else None,
        },
        "discount_count": int(df["has_discount"].sum()) if "has_discount" in df.columns else 0,
    }

def _best_benefit(df: pd.DataFrame, top: int = 20) -> List[Dict[str, Any]]:
    d = df.dropna(subset=["price"]).copy()
    d = d.assign(benefit=(d["rating"].fillna(0) / d["price"]))
    d = d.dropna(subset=["benefit"]).sort_values("benefit", ascending=False).head(top)
    out: List[Dict[str, Any]] = []
    for _, r in d.iterrows():
        out.append({
            "title": r.get("title"),
            "price": float(r.get("price")) if pd.notna(r.get("price")) else None,
            "rating": float(r.get("rating")) if pd.notna(r.get("rating")) else None,
            "benefit": float(r.get("benefit")) if pd.notna(r.get("benefit")) else None,
            "url": r.get("url"),
        })
    return out

def _sentiment(items: List[Dict], max_reviews: int = 300) -> Dict[str, Any]:
    texts: List[str] = []
    for it in items:
        for rv in it.get("reviews") or []:
            t = rv.get("content") or rv.get("title")
            if isinstance(t, str) and t.strip():
                texts.append(t.strip())
                if len(texts) >= max_reviews:
                    break
        if len(texts) >= max_reviews:
            break
    if not texts:
        return {"count": 0, "positive": 0, "negative": 0, "neutral": 0, "avg_score": None}
    # Intenta un modelo multilingüe (POS/NEG/NEU)
    try:
        from transformers import pipeline
        clf = pipeline("sentiment-analysis", model="cardiffnlp/twitter-xlm-roberta-base-sentiment")
        pos = neg = neu = 0
        score_acc = 0.0
        for t in texts:
            out = clf(t[:512])[0]
            label = out.get("label")
            score = float(out.get("score") or 0.0)
            if label == "positive":
                pos += 1; score_acc += score
            elif label == "negative":
                neg += 1; score_acc -= score
            else:
                neu += 1
        avg = score_acc / len(texts) if texts else 0.0
        return {"count": len(texts), "positive": pos, "negative": neg, "neutral": neu, "avg_score": avg}
    except Exception:
        # Fallback a flair (POS/NEG)
        try:
            from flair.models import TextClassifier
            from flair.data import Sentence
            clf = TextClassifier.load("sentiment-fast")
            pos = neg = 0
            score_acc = 0.0
            for t in texts:
                s = Sentence(t)
                clf.predict(s)
                lab = s.labels[0].value if s.labels else None
                sc = float(s.labels[0].score) if s.labels else 0.0
                if lab == "POSITIVE":
                    pos += 1; score_acc += sc
                elif lab == "NEGATIVE":
                    neg += 1; score_acc -= sc
            avg = score_acc / len(texts) if texts else 0.0
            return {"count": len(texts), "positive": pos, "negative": neg, "neutral": 0, "avg_score": avg}
        except Exception:
            return {"count": len(texts), "positive": None, "negative": None, "neutral": None, "avg_score": None}

def run_analysis(items: List[Dict]) -> Dict[str, Any]:
    df = to_dataframe(items)
    return {
        "summary": _summary(df),
        "histogram_price": _histogram(df["price"], bins=30),
        "sentiment": _sentiment(items),
        "reviews_report": _reviews_report(items),
    }

def _reviews_report(items: List[Dict]) -> Dict[str, Any]:
    products: List[Dict[str, Any]] = []
    for it in items:
        revs = it.get("reviews") or []
        vals: List[int] = []
        for rv in revs:
            r = rv.get("rate")
            if isinstance(r, (int, float)):
                v = int(r)
                if 0 < v <= 5:
                    vals.append(v)
        if not vals:
            continue
        avg = sum(vals) / len(vals)
        pos = sum(1 for v in vals if v >= 4)
        pct = (pos / len(vals)) if len(vals) else 0.0
        products.append({
            "title": it.get("title"),
            "avg_rating": avg,
            "reviews_count": len(vals),
            "positive_pct": pct,
            "url": it.get("url"),
        })
    ranking = sorted(products, key=lambda x: (-x["avg_rating"], -x["reviews_count"], str(x.get("title") or "")))[:max(10, len(products))]
    top3 = [p for p in ranking if p["avg_rating"] >= 4.5 and p["reviews_count"] >= 10][:3]
    star = None
    if products:
        best_all = sorted(products, key=lambda x: (-x["avg_rating"], -x["reviews_count"]))
        for p in best_all:
            if p["reviews_count"] >= 20:
                star = p
                break
    best_reviews_by_product: List[Dict[str, Any]] = []
    for it in items:
        revs = it.get("reviews") or []
        if not isinstance(revs, list):
            continue
        toks = [t.lower() for t in str(it.get("title") or "").split() if len(t) >= 3]
        cand: List[Dict[str, Any]] = []
        for rv in revs:
            rate = rv.get("rate")
            txt = rv.get("content") or rv.get("title") or ""
            if not isinstance(txt, str):
                continue
            s = txt.strip()
            if not s or len(s) < 100:
                continue
            if not isinstance(rate, (int, float)) or int(rate) != 5:
                continue
            low = s.lower()
            hits = sum(1 for tk in toks if tk in low)
            if hits < 1:
                continue
            cand.append({
                "rate": int(rate),
                "date": rv.get("date"),
                "content": s,
            })
        cand = sorted(cand, key=lambda r: (-len(str(r.get("content") or "")), r.get("date") or ""))[:3]
        best_reviews_by_product.append({
            "title": it.get("title"),
            "reviews": cand,
        })
    return {
        "products": products,
        "ranking": ranking[:10],
        "top3": top3,
        "star_product": star,
        "best_reviews_by_product": best_reviews_by_product,
    }


def run():
    parser = argparse.ArgumentParser(description="Scraper de Mercado Libre Colombia")
    parser.add_argument("keyword", nargs="?", help="Palabra clave a buscar, p.ej. 'telefono'")
    parser.add_argument("--url", dest="url", help="URL de listado de Mercado Libre")
    parser.add_argument("--max-pages", type=int, default=5, dest="max_pages", help="Máximo de páginas a recorrer")
    parser.add_argument("--per-page-delay", type=float, default=1.5, dest="per_page_delay", help="Delay entre páginas (segundos)")
    parser.add_argument("--detail-delay", type=float, default=1.0, dest="detail_delay", help="Delay entre detalles (segundos)")
    parser.add_argument("--out", default=None, help="Ruta de salida JSON (opcional)")
    parser.add_argument("--java-url", dest="java_url", default=os.environ.get("JAVA_API_URL", "http://localhost:8080"))
    parser.add_argument("--token", dest="token", default=os.environ.get("PYTHON_SERVICE_TOKEN"))
    parser.add_argument("--save-json", action="store_true", dest="save_json")
    # Flags de storage_state removidos para volver al estado base
    args = parser.parse_args()

    # Sin guardado de storage_state en estado base

    if args.url:
        results = scrape_listing_from_url(
            url=args.url,
            max_pages=args.max_pages,
            per_page_delay=args.per_page_delay,
            detail_delay=args.detail_delay,
        )
        source = args.url
        default_name = "listado"
    else:
        results = scrape_listing(
            keyword=args.keyword,
            max_pages=args.max_pages,
            per_page_delay=args.per_page_delay,
            detail_delay=args.detail_delay,
        )
        source = args.keyword
        default_name = (args.keyword or "listado").replace(" ", "_")

    logging.basicConfig(level=logging.INFO)
    ok = send_results_to_java(results, source, args.java_url, args.token)
    print(f"Enviado {len(results)} productos a: {args.java_url}/api/data ok={ok}")
    try:
        _mongo_upsert_items(results, source)
        print(f"MongoDB actualizado para '{source}'")
    except Exception as e:
        print(f"MongoDB error: {e}")
    if args.save_json:
        out_dir = Path("data")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = args.out or out_dir / f"{default_name}.json"
        out_file = str(out_file)
        save_results_to_json(results, source, out_file)
        print(f"Guardado {len(results)} productos en: {out_file}")
    

def _mongo_db():
    uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/scraping")
    client = MongoClient(uri)
    try:
        dbname = uri.rsplit('/', 1)[-1]
        db = client[dbname]
    except Exception:
        db = client["scraping"]
    return db

def _item_hash(d: Dict[str, Any]) -> str:
    keys = ["title","url","image","price","discount_price","rating","rating_count","sold","description"]
    payload = {k: d.get(k) for k in keys}
    s = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _mongo_upsert_items(items: List[Dict], keyword: str):
    db = _mongo_db()
    col = db["products"]
    ops: List[UpdateOne] = []
    for it in items:
        url = it.get("url")
        if not isinstance(url, str):
            continue
        doc = {
            "title": it.get("title"),
            "url": url,
            "image": it.get("image"),
            "price": it.get("price"),
            "discount_price": it.get("discount_price"),
            "rating": it.get("rating"),
            "rating_count": it.get("rating_count"),
            "sold": it.get("sold"),
            "description": it.get("description"),
            "keyword": keyword,
            "reviews": it.get("reviews") or [],
        }
        h = _item_hash(doc)
        existing = col.find_one({"url": url}, {"item_hash": 1})
        if existing and existing.get("item_hash") == h:
            continue
        ops.append(UpdateOne({"url": url}, {"$set": {**doc, "item_hash": h}}, upsert=True))
    if ops:
        col.bulk_write(ops, ordered=False)

def mongo_get_items(keyword: str) -> List[Dict]:
    db = _mongo_db()
    col = db["products"]
    cur = col.find({"keyword": {"$regex": keyword, "$options": "i"}})
    out: List[Dict] = []
    for d in cur:
        d.pop("_id", None)
        d.pop("item_hash", None)
        out.append(d)
    return out

if __name__ == "__main__":
    run()