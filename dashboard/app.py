"""KSH SERP Tracker dashboard.

Reads data/serp.db (populated by ksh_serp.scraper) and renders 4 tabs:
- Overview: top-line SERP environment metrics
- Brand Defense: per-query brand SERP composition
- Non-Brand Pages: page-by-page nonbrand tracker
- AIO Citations: scoreboard of AIO source mentions for KSH
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "serp.db"
KEYWORDS_CSV = ROOT / "data" / "keywords.csv"

JSON_COLS = ("aio_sources", "ota_ads", "top_3_organic_domains")

st.set_page_config(
    page_title="KSH SERP Tracker",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=300)
def load_df() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    with sqlite3.connect(DB_PATH) as con:
        df = pd.read_sql("SELECT * FROM serp_runs", con)
    if df.empty:
        return df
    df["run_date"] = pd.to_datetime(df["run_date"])
    for c in JSON_COLS:
        df[c] = df[c].apply(json.loads)
    if KEYWORDS_CSV.exists():
        kw = pd.read_csv(KEYWORDS_CSV)
        df = df.merge(kw[["query", "page"]], on="query", how="left")
    return df


st.title("Kauai Shores Hotel — SERP Environment Tracker")
st.caption(
    "Weekly snapshot of what AI Overviews, OTAs, and the Hotel Pack are doing to our SERP. "
    "Data via SerpAPI. See `docs/superpowers/plans/2026-05-20-ksh-serp-tracker.md` for design."
)

df = load_df()
if df.empty:
    st.warning(
        "No data yet. Run the scraper first:\n\n"
        "```bash\npython -m ksh_serp.scraper\n```"
    )
    st.stop()

with st.sidebar:
    st.header("Filters")
    device_filter = st.radio("Device", ["both", "desktop", "mobile"], horizontal=True)
    latest = df["run_date"].max()
    st.metric("Latest run", latest.strftime("%Y-%m-%d"))
    st.metric("Total rows", len(df))
    st.metric("Unique queries", df["query"].nunique())

if device_filter != "both":
    df = df[df["device"] == device_filter]

tab_overview, tab_brand, tab_pages, tab_citations = st.tabs(
    ["Overview", "Brand Defense", "Non-Brand Pages", "AIO Citations"]
)

# ============================================================
# Tab 1: Overview
# ============================================================
with tab_overview:
    st.subheader("SERP Environment Overview")

    latest_df = df[df["run_date"] == df["run_date"].max()]
    brand_latest = latest_df[latest_df["query_type"] == "brand"]
    nonbrand_latest = latest_df[latest_df["query_type"] == "nonbrand"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Brand queries w/ AIO",
        f"{brand_latest['aio_present'].mean() * 100:.0f}%" if len(brand_latest) else "—",
    )
    c2.metric(
        "Non-brand queries w/ AIO",
        f"{nonbrand_latest['aio_present'].mean() * 100:.0f}%" if len(nonbrand_latest) else "—",
    )
    c3.metric(
        "Avg ads on brand SERP",
        f"{brand_latest['ads_count'].mean():.1f}" if len(brand_latest) else "—",
    )
    c4.metric(
        "Hotel Pack presence",
        f"{latest_df['hotel_pack_present'].mean() * 100:.0f}%" if len(latest_df) else "—",
    )

    st.divider()

    trend = (
        df.groupby(["run_date", "query_type"])["aio_present"]
        .mean()
        .reset_index()
    )
    trend["aio_present"] *= 100
    fig_aio = px.line(
        trend, x="run_date", y="aio_present", color="query_type",
        title="AI Overview presence over time (%)",
        labels={"aio_present": "% of queries with AIO", "run_date": ""},
    )
    st.plotly_chart(fig_aio, use_container_width=True)

    ota_trend = (
        df[df["query_type"] == "brand"]
        .assign(ota_count=lambda d: d["ota_ads"].apply(len))
        .groupby("run_date")["ota_count"]
        .mean()
        .reset_index()
    )
    fig_ota = px.line(
        ota_trend, x="run_date", y="ota_count",
        title="Avg OTA paid ads above organic — brand SERP",
        labels={"ota_count": "Avg # OTA ads", "run_date": ""},
    )
    st.plotly_chart(fig_ota, use_container_width=True)


# ============================================================
# Tab 2: Brand Defense
# ============================================================
with tab_brand:
    st.subheader("Brand Defense Board")
    st.caption("Top brand queries — what's stacked above our organic listing")

    brand = df[df["query_type"] == "brand"].copy()
    latest_brand = brand[brand["run_date"] == brand["run_date"].max()].copy()
    latest_brand["ota_ads_count"] = latest_brand["ota_ads"].apply(len)
    latest_brand["ota_domains"] = latest_brand["ota_ads"].apply(
        lambda L: ", ".join(sorted({a["domain"] for a in L}))
    )
    latest_brand["aio_sources_domains"] = latest_brand["aio_sources"].apply(
        lambda L: ", ".join(sorted({s["domain"] for s in L if s.get("domain")}))
    )

    cols = [
        "query", "device", "aio_present", "ksh_cited_in_aio",
        "ads_count", "ota_ads_count", "ota_domains",
        "ksh_organic_pos", "ksh_in_hotel_pack",
    ]
    st.dataframe(
        latest_brand[cols].rename(columns={
            "ads_count": "total ads",
            "ota_ads_count": "OTA ads",
            "ota_domains": "OTA domains",
            "aio_present": "AIO?",
            "ksh_cited_in_aio": "KSH cited?",
            "ksh_organic_pos": "KSH org pos",
            "ksh_in_hotel_pack": "KSH in pack?",
        }),
        use_container_width=True, hide_index=True,
    )

    st.divider()
    st.markdown("##### KSH organic position trend (brand queries)")
    pos_trend = (
        brand.dropna(subset=["ksh_organic_pos"])
        .groupby(["run_date", "device"])["ksh_organic_pos"]
        .mean()
        .reset_index()
    )
    if not pos_trend.empty:
        fig_pos = px.line(
            pos_trend, x="run_date", y="ksh_organic_pos", color="device",
            title="Avg KSH organic position on brand queries (lower = better)",
            labels={"ksh_organic_pos": "avg position"},
        )
        fig_pos.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_pos, use_container_width=True)


# ============================================================
# Tab 3: Non-Brand Pages
# ============================================================
with tab_pages:
    st.subheader("Non-Brand Page Tracker")
    st.caption(
        "The 4 pages with concentrated impression loss. "
        "Track AIO presence, KSH ranking, and Hotel Pack competition per page."
    )

    nonbrand = df[df["query_type"] == "nonbrand"].copy()
    if "page" not in nonbrand.columns:
        st.warning("Page column missing — check data/keywords.csv has a `page` column.")
    else:
        pages = ["/", "/dining", "/specials", "/rooms"]
        for p in pages:
            st.markdown(f"### `{p}`")
            page_df = nonbrand[nonbrand["page"] == p]
            if page_df.empty:
                st.info(f"No nonbrand queries assigned to `{p}` in keywords.csv.")
                continue
            latest = page_df[page_df["run_date"] == page_df["run_date"].max()].copy()
            latest["top_3"] = latest["top_3_organic_domains"].apply(
                lambda L: ", ".join(L[:3])
            )
            latest["aio_sources_count"] = latest["aio_sources"].apply(len)
            cols = [
                "query", "device", "aio_present", "aio_sources_count",
                "ksh_organic_pos", "hotel_pack_present", "ksh_in_hotel_pack", "top_3",
            ]
            st.dataframe(
                latest[cols].rename(columns={
                    "aio_present": "AIO?",
                    "aio_sources_count": "# AIO sources",
                    "ksh_organic_pos": "KSH org pos",
                    "hotel_pack_present": "Hotel pack?",
                    "ksh_in_hotel_pack": "KSH in pack?",
                    "top_3": "top 3 organic",
                }),
                use_container_width=True, hide_index=True,
            )


# ============================================================
# Tab 4: AIO Citation Scoreboard
# ============================================================
with tab_citations:
    st.subheader("AIO Citation Scoreboard")
    st.caption(
        "Queries where kauaishoreshotel.com is cited as a source in AI Overviews. "
        "This is the citation game — schema + FAQ work pays off here."
    )

    cited = df[df["ksh_cited_in_aio"] == 1].copy()
    if cited.empty:
        st.info(
            "No AIO citations earned yet. Work the schema + FAQ play "
            "(Hotel/Restaurant/Offer/FAQPage on home, dining, specials, rooms) "
            "to start landing here."
        )
    else:
        latest = cited[cited["run_date"] == cited["run_date"].max()]
        st.markdown(f"**{len(latest)}** citation(s) in latest run ({latest['run_date'].max().date()})")
        st.dataframe(
            latest[["query", "query_type", "device", "run_date"]],
            use_container_width=True, hide_index=True,
        )

        st.divider()
        over_time = cited.groupby("run_date").size().reset_index(name="citations")
        fig = px.bar(
            over_time, x="run_date", y="citations",
            title="AIO citations earned over time",
        )
        st.plotly_chart(fig, use_container_width=True)
