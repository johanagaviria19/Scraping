import os
from pathlib import Path
from typing import List, Dict

import streamlit as st
import pandas as pd
import altair as alt

from scraper.mercadolibre import scrape_listing, scrape_listing_from_url, save_results_to_json
import re


st.set_page_config(page_title="Comparador Mercado Libre", layout="wide")


@st.cache_data(show_spinner=False)
def _scrape(source: str, max_pages: int, per_page_delay: float, detail_delay: float) -> List[Dict]:
    s = (source or "").strip()
    if s.lower().startswith("http"):
        return scrape_listing_from_url(s, max_pages=max_pages, per_page_delay=per_page_delay, detail_delay=detail_delay)
    return scrape_listing(s, max_pages=max_pages, per_page_delay=per_page_delay, detail_delay=detail_delay)


def _safe_name(source: str) -> str:
    s = (source or "").strip().replace(" ", "_")
    s = re.sub(r"[^A-Za-z0-9_.-]", "_", s)
    return s[:80] if len(s) > 80 else s


def _to_dataframe(items: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(items)
    # Asegurar columnas esperadas
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

    # Normalización de tipos numéricos
    for col in ["price", "discount_price", "rating", "rating_count", "sold"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Métricas derivadas
    df["has_discount"] = df["discount_price"].notna()
    price = df["price"].copy()
    price = price.where(price > 0)  # evita división por cero o negativos
    df["benefit"] = (df["rating"].fillna(0)) / price
    return df


def sidebar_controls():
    st.sidebar.header("Búsqueda")
    keyword = st.sidebar.text_input("Palabra clave o URL", value="telefono")
    max_pages = st.sidebar.slider("Máx. páginas", 1, 20, 5)
    per_page_delay = st.sidebar.slider("Delay por página (s)", 0.5, 5.0, 1.5)
    detail_delay = st.sidebar.slider("Delay por detalle (s)", 0.5, 5.0, 1.0)
    run_search = st.sidebar.button("Buscar y actualizar datos")
    return keyword, max_pages, per_page_delay, detail_delay, run_search


def render_dashboard(df: pd.DataFrame):
    st.title("Dashboard comparativo de Mercado Libre")

    # Filtros básicos
    col1, col2, col3 = st.columns(3)
    with col1:
        price_series = pd.to_numeric(df["price"], errors="coerce")
        pmin = price_series.dropna().min()
        pmax = price_series.dropna().max()
        min_price = float(pmin) if pd.notna(pmin) else 0.0
        max_price = float(pmax) if pd.notna(pmax) else 0.0
        if max_price <= min_price:
            max_price = min_price + 1.0
        price_range = st.slider("Rango de precio", min_price, max_price, (min_price, max_price))
    with col2:
        rating_series = pd.to_numeric(df["rating"], errors="coerce")
        rmin = rating_series.dropna().min()
        rmax = rating_series.dropna().max()
        min_rating = float(rmin) if pd.notna(rmin) else 0.0
        max_rating = float(rmax) if pd.notna(rmax) else 5.0
        if max_rating <= min_rating:
            max_rating = min_rating + 1.0
        rating_range = st.slider("Rango de calificación", min_rating, max_rating, (min_rating, max_rating))
    with col3:
        only_discount = st.checkbox("Solo productos con descuento", value=False)

    fdf = df.copy()
    if pd.notna(pmin) and pd.notna(pmax):
        fdf = fdf[(fdf["price"] >= price_range[0]) & (fdf["price"] <= price_range[1])]
    fdf = fdf[(fdf["rating"].fillna(0) >= rating_range[0]) & (fdf["rating"].fillna(0) <= rating_range[1])]
    if only_discount:
        fdf = fdf[fdf["has_discount"]]

    # Tabla filtrable y ordenable
    st.subheader("Tabla de productos")
    display_cols = [
        c for c in ["title", "price", "discount_price", "rating", "rating_count", "sold", "benefit", "url"]
        if c in fdf.columns
    ]
    st.dataframe(fdf[display_cols], use_container_width=True)

    # Gráficas
    st.subheader("Distribución de precios")
    price_df = fdf.dropna(subset=["price"]).copy()
    if not price_df.empty:
        price_hist = alt.Chart(price_df).mark_bar().encode(
            alt.X("price", bin=alt.Bin(maxbins=30), title="Precio"),
            alt.Y("count()", title="Cantidad"),
            tooltip=["count()"],
        ).properties(height=300)
        st.altair_chart(price_hist, use_container_width=True)
    else:
        st.info("Sin datos para la distribución de precios")

    st.subheader("Top productos por reseñas")
    top_reviews = fdf.dropna(subset=["rating"]).copy()
    if not top_reviews.empty:
        top_reviews = top_reviews.sort_values(["rating", "rating_count"], ascending=False).head(20)
        review_chart = alt.Chart(top_reviews).mark_bar().encode(
            x=alt.X("title", sort="-y", title="Producto"),
            y=alt.Y("rating", title="Calificación"),
            color=alt.Color("rating_count", title="# Reseñas"),
            tooltip=["rating", "rating_count", "price"],
        ).properties(height=300)
        st.altair_chart(review_chart, use_container_width=True)
    else:
        st.info("Sin datos de reseñas para graficar")

    st.subheader("Mejor relación precio-beneficio")
    best_benefit = fdf.dropna(subset=["price"]).copy()
    if not best_benefit.empty:
        best_benefit = best_benefit.assign(benefit=(best_benefit["rating"].fillna(0) / best_benefit["price"]))
        top_benefit = best_benefit.dropna(subset=["benefit"]).sort_values("benefit", ascending=False).head(20)
        if not top_benefit.empty:
            benefit_chart = alt.Chart(top_benefit).mark_bar().encode(
                x=alt.X("title", sort="-y", title="Producto"),
                y=alt.Y("benefit", title="Beneficio (rating/precio)"),
                tooltip=["benefit", "rating", "price"],
            ).properties(height=300)
            st.altair_chart(benefit_chart, use_container_width=True)
        else:
            st.info("Sin datos para relación precio-beneficio")
    else:
        st.info("Sin datos de precio para calcular beneficio")


def main():
    keyword, max_pages, per_page_delay, detail_delay, run_search = sidebar_controls()

    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = data_dir / f"{_safe_name(keyword)}.json"

    if run_search:
        with st.spinner("Scrapeando Mercado Libre..."):
            items = _scrape(keyword, max_pages, per_page_delay, detail_delay)
            save_results_to_json(items, keyword, str(json_path))
        st.success(f"Datos actualizados: {json_path}")

    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            data = pd.read_json(f)
        df = _to_dataframe(list(data["items"]))
        render_dashboard(df)
    else:
        st.info("Ejecuta una búsqueda para generar datos.")


if __name__ == "__main__":
    main()