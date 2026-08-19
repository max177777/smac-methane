"""
Comparison page.
Pick two SMAC subnational jurisdictions and two years, side by side: sector
breakdown, data table, and multi-year sector-composition trend for each.
Subnational only — the dataset only covers actual SMAC member/observer
jurisdictions, not comprehensive country-wide data, so a "country total" would
just be the sum of a country's SMAC members, not a real national figure.
"""

import plotly.graph_objects as go
import streamlit as st

from utils.theme import inject_theme, eyebrow, render_footer
from utils.data_loader import (
    COUNTRY_META, COUNTRY_ORDER, CURRENT_YEAR, SECTOR_ORDER,
    list_locations, location_sectors, sector_yearly_series, display_name,
    fmt_int, fmt_mt,
)
from utils.charts import SECTOR_COLORS, INK, INK_SOFT, LINE_SOFT, PAPER

inject_theme()

YEARS = list(range(2021, CURRENT_YEAR + 2))  # includes the partial current-year+1 (2026)

eyebrow("Comparison")
st.markdown("<h1>Compare CH₄ <em>emissions</em></h1>", unsafe_allow_html=True)
st.markdown(
    '<div class="smac-meta" style="margin-bottom:18px;">'
    'pick any two SMAC jurisdictions and compare side by side</div>',
    unsafe_allow_html=True,
)


def _picker(side: str):
    """Renders Country + Subnational + Year pickers for one side ('A' or 'B').
    Returns (iso, location, year)."""
    st.markdown(f"<h3 style='margin-bottom:10px;'>Location {side}</h3>", unsafe_allow_html=True)
    iso = st.selectbox(
        f"Country {side}", options=COUNTRY_ORDER,
        format_func=lambda x: COUNTRY_META[x]["name"],
        key=f"cmp_country_{side}",
    )
    locs = list_locations(iso)
    location = st.selectbox(f"Subnational unit {side}", options=locs,
                            format_func=display_name, key=f"cmp_loc_{side}")
    year = st.selectbox(f"Year {side}", options=list(reversed(YEARS)),
                        index=YEARS[::-1].index(CURRENT_YEAR), key=f"cmp_year_{side}")
    return iso, location, year


col_a, col_b = st.columns(2, gap="large")
with col_a:
    iso_a, loc_a, year_a = _picker("A")
with col_b:
    iso_b, loc_b, year_b = _picker("B")

st.markdown("<br>", unsafe_allow_html=True)


def _sector_df(iso, location, year):
    return location_sectors(iso, location, year)


def _sector_bar(sec_df, title, key):
    fig = go.Figure()
    ordered = [s for s in SECTOR_ORDER if s in set(sec_df["sector"])]
    vals = sec_df.set_index("sector").reindex(ordered)["total_emission"].fillna(0)
    fig.add_trace(go.Bar(
        x=ordered, y=vals.values,
        marker_color=[SECTOR_COLORS.get(s, "#b9c4bd") for s in ordered],
    ))
    fig.update_layout(
        height=340, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=60),
        xaxis=dict(tickfont=dict(size=10, family="Quicksand, sans-serif"), tickangle=-30),
        yaxis=dict(gridcolor=LINE_SOFT, tickfont=dict(size=10, family="Quicksand, sans-serif")),
        font=dict(family="Inter, sans-serif", color=INK),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)


def _trend_chart(iso, location, key):
    df = sector_yearly_series(iso, location)
    df = df[df["year"] <= CURRENT_YEAR + 1]
    fig = go.Figure()
    for s in SECTOR_ORDER:
        sub = df[df["sector"] == s].sort_values("year")
        if sub.empty:
            continue
        fig.add_trace(go.Bar(
            x=sub["year"], y=sub["ch4_tonnes"], name=s,
            marker_color=SECTOR_COLORS.get(s, "#b9c4bd"),
        ))
    fig.update_layout(
        barmode="stack", height=340, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(dtick=1, tickfont=dict(size=10, family="Quicksand, sans-serif")),
        yaxis=dict(gridcolor=LINE_SOFT, title="CH₄ tonnes", tickfont=dict(size=10, family="Quicksand, sans-serif")),
        legend=dict(orientation="v", font=dict(size=9, family="Quicksand, sans-serif")),
        font=dict(family="Inter, sans-serif", color=INK),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)


# ============== SECTOR BREAKDOWN ==============
label_a = f"{display_name(loc_a)} ({COUNTRY_META[iso_a]['name']})"
label_b = f"{display_name(loc_b)} ({COUNTRY_META[iso_b]['name']})"

sec_a = _sector_df(iso_a, loc_a, year_a)
sec_b = _sector_df(iso_b, loc_b, year_b)

st.markdown(f"<h3>{label_a} ({year_a}) vs {label_b} ({year_b}) — sector breakdown</h3>", unsafe_allow_html=True)
bar_a, bar_b = st.columns(2, gap="large")
with bar_a:
    st.markdown(f'<div class="smac-meta">{label_a} · CH₄ by sector · {year_a}</div>', unsafe_allow_html=True)
    if sec_a.empty:
        st.info(f"No {year_a} data for {label_a}.")
    else:
        _sector_bar(sec_a, label_a, "chart_sec_a")
with bar_b:
    st.markdown(f'<div class="smac-meta">{label_b} · CH₄ by sector · {year_b}</div>', unsafe_allow_html=True)
    if sec_b.empty:
        st.info(f"No {year_b} data for {label_b}.")
    else:
        _sector_bar(sec_b, label_b, "chart_sec_b")

st.markdown("<br>", unsafe_allow_html=True)

# ============== DATA TABLE ==============
st.markdown("<h3>Data table</h3>", unsafe_allow_html=True)
tbl_a, tbl_b = st.columns(2, gap="large")
with tbl_a:
    st.markdown(f'<div class="smac-meta">Data table · {label_a}</div>', unsafe_allow_html=True)
    st.dataframe(
        sec_a.rename(columns={"sector": "Sector", "total_emission": f"{year_a} CH₄ (t)"}),
        hide_index=True, use_container_width=True,
        column_config={f"{year_a} CH₄ (t)": st.column_config.NumberColumn(format="%d")},
    )
with tbl_b:
    st.markdown(f'<div class="smac-meta">Data table · {label_b}</div>', unsafe_allow_html=True)
    st.dataframe(
        sec_b.rename(columns={"sector": "Sector", "total_emission": f"{year_b} CH₄ (t)"}),
        hide_index=True, use_container_width=True,
        column_config={f"{year_b} CH₄ (t)": st.column_config.NumberColumn(format="%d")},
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============== MULTI-YEAR TREND ==============
st.markdown("<h3>CH₄ emissions trend by sector</h3>", unsafe_allow_html=True)
trend_a, trend_b = st.columns(2, gap="large")
with trend_a:
    st.markdown(f'<div class="smac-meta">{label_a} · CH₄ by sector · {2021}–{CURRENT_YEAR + 1}</div>', unsafe_allow_html=True)
    _trend_chart(iso_a, loc_a, "chart_trend_a")
with trend_b:
    st.markdown(f'<div class="smac-meta">{label_b} · CH₄ by sector · {2021}–{CURRENT_YEAR + 1}</div>', unsafe_allow_html=True)
    _trend_chart(iso_b, loc_b, "chart_trend_b")


render_footer()
