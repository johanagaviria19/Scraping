import argparse
import os
from pathlib import Path

from scraper.mercadolibre import scrape_listing, scrape_listing_from_url, save_results_to_json


def run():
    parser = argparse.ArgumentParser(description="Scraper de Mercado Libre Colombia")
    parser.add_argument("keyword", nargs="?", help="Palabra clave a buscar, p.ej. 'telefono'")
    parser.add_argument("--url", dest="url", help="URL de listado de Mercado Libre")
    parser.add_argument("--max-pages", type=int, default=5, dest="max_pages", help="Máximo de páginas a recorrer")
    parser.add_argument("--per-page-delay", type=float, default=1.5, dest="per_page_delay", help="Delay entre páginas (segundos)")
    parser.add_argument("--detail-delay", type=float, default=1.0, dest="detail_delay", help="Delay entre detalles (segundos)")
    parser.add_argument("--out", default=None, help="Ruta de salida JSON (opcional)")
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
        default_name = args.keyword.replace(" ", "_")

    out_dir = Path("data")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = args.out or out_dir / f"{default_name}.json"
    out_file = str(out_file)

    save_results_to_json(results, source, out_file)
    print(f"Guardado {len(results)} productos en: {out_file}")


if __name__ == "__main__":
    run()