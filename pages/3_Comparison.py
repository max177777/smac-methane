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
from utils.i18n import t, sector_name, country_name

inject_theme()

YEARS = list(range(2021, CURRENT_YEAR + 2))  # includes the partial current-year+1 (2026)

eyebrow(t("nav.compare"))
st.markdown(f"<h1>{t('compare.title')}</h1>", unsafe_allow_html=True)
st.markdown(
    f'<div class="smac-meta" style="margin-bottom:18px;">{t("compare.subtitle")}</div>',
    unsafe_allow_html=True,
)


# Default to two DIFFERENT jurisdictions — a comparison page that opens with
# the same place on both sides shows nothing and makes the user do setup work
# before the page means anything.
DEFAULT_A = ("USA", "Maryland")
DEFAULT_B = ("CAN", "Alberta")


def _picker(side: str, default: tuple[str, str]):
    """Renders Country + Subnational + Year pickers for one side ('A' or 'B').
    Returns (iso, location, year)."""
    st.markdown(f"<h3 style='margin-bottom:10px;'>{t('compare.location', side=side)}</h3>", unsafe_allow_html=True)
    d_iso, d_loc = default
    iso = st.selectbox(
        t("compare.country", side=side), options=COUNTRY_ORDER,
        index=COUNTRY_ORDER.index(d_iso) if d_iso in COUNTRY_ORDER else 0,
        format_func=country_name,
        key=f"cmp_country_{side}",
    )
    locs = list_locations(iso)
    location = st.selectbox(
        t("compare.unit", side=side), options=locs,
        index=locs.index(d_loc) if d_loc in locs else 0,
        format_func=display_name, key=f"cmp_loc_{side}")
    year = st.selectbox(t("compare.year", side=side), options=list(reversed(YEARS)),
                        index=YEARS[::-1].index(CURRENT_YEAR), key=f"cmp_year_{side}")
    return iso, location, year


col_a, col_b = st.columns(2, gap="large")
with col_a:
    iso_a, loc_a, year_a = _picker("A", DEFAULT_A)
with col_b:
    iso_b, loc_b, year_b = _picker("B", DEFAULT_B)

st.markdown("<br>", unsafe_allow_html=True)


def _sector_df(iso, location, year):
    return location_sectors(iso, location, year)


def _sector_bar(sec_df, title, key, y_max=None):
    fig = go.Figure()
    ordered = [s for s in SECTOR_ORDER if s in set(sec_df["sector"])]
    vals = sec_df.set_index("sector").reindex(ordered)["total_emission"].fillna(0)
    fig.add_trace(go.Bar(
        x=[sector_name(x) for x in ordered], y=vals.values,
        marker_color=[SECTOR_COLORS.get(s, "#b9c4bd") for s in ordered],
    ))
    fig.update_layout(
        height=340, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=60),
        xaxis=dict(tickfont=dict(size=10, family="Quicksand, sans-serif"), tickangle=-30),
        yaxis=dict(gridcolor=LINE_SOFT, tickfont=dict(size=10, family="Quicksand, sans-serif"),
                   range=[0, y_max] if y_max else None),
        font=dict(family="Inter, sans-serif", color=INK),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)


def _trend_chart(iso, location, key, y_max=None):
    df = sector_yearly_series(iso, location)
    df = df[df["year"] <= CURRENT_YEAR + 1]
    fig = go.Figure()
    for s in SECTOR_ORDER:
        sub = df[df["sector"] == s].sort_values("year")
        if sub.empty:
            continue
        fig.add_trace(go.Bar(
            x=sub["year"], y=sub["ch4_tonnes"], name=sector_name(s),
            marker_color=SECTOR_COLORS.get(s, "#b9c4bd"),
        ))
    fig.update_layout(
        barmode="stack", height=340, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(dtick=1, tickfont=dict(size=10, family="Quicksand, sans-serif")),
        yaxis=dict(gridcolor=LINE_SOFT, title=t("common.ch4_tonnes"),
                   tickfont=dict(size=10, family="Quicksand, sans-serif"),
                   range=[0, y_max] if y_max else None),
        legend=dict(orientation="v", font=dict(size=9, family="Quicksand, sans-serif")),
        font=dict(family="Inter, sans-serif", color=INK),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)


# ============== SECTOR BREAKDOWN ==============
label_a = f"{display_name(loc_a)} ({country_name(iso_a)})"
label_b = f"{display_name(loc_b)} ({country_name(iso_b)})"

sec_a = _sector_df(iso_a, loc_a, year_a)
sec_b = _sector_df(iso_b, loc_b, year_b)

# Each panel scales to its own maximum by default, so both breakdowns stay
# readable — pairs can differ by 30x or more (Maryland's largest sector is
# ~64 kt against Alberta's ~2.3 Mt), and on a shared axis the smaller one is
# nearly flat and tells you nothing about its own composition.
#
# The cost is that bar HEIGHTS are then not comparable across the two sides,
# even though the side-by-side layout invites exactly that reading. The toggle
# below switches to a shared axis for anyone who wants the absolute comparison;
# the axis labels always show the real numbers either way.
_shared_scale = st.checkbox(
    t("compare.same_scale"),
    value=False,
    help=t("compare.same_scale_help"),
)
_sector_ymax = max(
    [float(sec_a["total_emission"].max()) if not sec_a.empty else 0,
     float(sec_b["total_emission"].max()) if not sec_b.empty else 0]) * 1.08 or None
_sector_ymax = _sector_ymax if _shared_scale else None

_ta = sector_yearly_series(iso_a, loc_a)
_tb = sector_yearly_series(iso_b, loc_b)
_trend_ymax = max(
    [float(_ta.groupby("year")["ch4_tonnes"].sum().max()) if not _ta.empty else 0,
     float(_tb.groupby("year")["ch4_tonnes"].sum().max()) if not _tb.empty else 0]) * 1.08 or None
_trend_ymax = _trend_ymax if _shared_scale else None

st.markdown(f"<h3>{t('compare.breakdown_h3', a=label_a, ya=year_a, b=label_b, yb=year_b)}</h3>", unsafe_allow_html=True)
bar_a, bar_b = st.columns(2, gap="large")
with bar_a:
    st.markdown(f'<div class="smac-meta">{t("compare.by_sector", label=label_a, y=year_a)}</div>', unsafe_allow_html=True)
    if sec_a.empty:
        st.info(t("compare.no_data", y=year_a, label=label_a))
    else:
        _sector_bar(sec_a, label_a, "chart_sec_a", y_max=_sector_ymax)
with bar_b:
    st.markdown(f'<div class="smac-meta">{t("compare.by_sector", label=label_b, y=year_b)}</div>', unsafe_allow_html=True)
    if sec_b.empty:
        st.info(t("compare.no_data", y=year_b, label=label_b))
    else:
        _sector_bar(sec_b, label_b, "chart_sec_b", y_max=_sector_ymax)

st.markdown("<br>", unsafe_allow_html=True)

# ============== DATA TABLE ==============
st.markdown(f"<h3>{t('compare.table')}</h3>", unsafe_allow_html=True)
tbl_a, tbl_b = st.columns(2, gap="large")
with tbl_a:
    st.markdown(f'<div class="smac-meta">{t("compare.table")} · {label_a}</div>', unsafe_allow_html=True)
    _col = t("common.ch4_t_col", y=year_a)
    st.dataframe(
        sec_a.assign(sector=sec_a["sector"].map(sector_name))
        .rename(columns={"sector": t("common.sector"), "total_emission": _col}),
        hide_index=True, use_container_width=True,
        column_config={_col: st.column_config.NumberColumn(format="localized")},
    )
with tbl_b:
    st.markdown(f'<div class="smac-meta">{t("compare.table")} · {label_b}</div>', unsafe_allow_html=True)
    _col = t("common.ch4_t_col", y=year_b)
    st.dataframe(
        sec_b.assign(sector=sec_b["sector"].map(sector_name))
        .rename(columns={"sector": t("common.sector"), "total_emission": _col}),
        hide_index=True, use_container_width=True,
        column_config={_col: st.column_config.NumberColumn(format="localized")},
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============== MULTI-YEAR TREND ==============
st.markdown(f"<h3>{t('compare.trend_h3')}</h3>", unsafe_allow_html=True)
trend_a, trend_b = st.columns(2, gap="large")
with trend_a:
    st.markdown(f'<div class="smac-meta">{t("compare.by_sector", label=label_a, y=f"2021–{CURRENT_YEAR + 1}")}</div>', unsafe_allow_html=True)
    _trend_chart(iso_a, loc_a, "chart_trend_a", y_max=_trend_ymax)
with trend_b:
    st.markdown(f'<div class="smac-meta">{t("compare.by_sector", label=label_b, y=f"2021–{CURRENT_YEAR + 1}")}</div>', unsafe_allow_html=True)
    _trend_chart(iso_b, loc_b, "chart_trend_b", y_max=_trend_ymax)


render_footer()
