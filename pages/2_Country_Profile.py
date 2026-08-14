"""
SMAC page — jurisdiction (not country) profile.
Every button is one actual SMAC member/observer subnational unit, color-coded by
country, sorted alphabetically by country then by jurisdiction. Shows that
jurisdiction's KPIs, time series, real sector breakdown, top emission sources, and a
quick-bullet Methane Action Plan built from those top sources.
"""

import re

import streamlit as st

from utils.theme import inject_theme, eyebrow
from utils.data_loader import (
    COUNTRY_META, COUNTRY_COLORS, CURRENT_YEAR, DATA_RANGE_LABEL,
    all_member_locations, member_status, location_yearly, location_monthly,
    location_yearly_ranking, location_sectors, top_sectors_pareto, action_plan_bullets,
    fmt_int, fmt_mt, pct_change, display_name,
)
from utils.policy_content import POLICY, GWP100, GWP20
from utils.charts import time_series_plotly, SECTOR_COLORS

inject_theme()


def _slug(iso: str, loc: str) -> str:
    return "jc-" + re.sub(r"[^a-z0-9]+", "-", f"{iso}-{loc}".lower()).strip("-")


# ============== JURISDICTION SELECTOR ==============
all_locs = all_member_locations()  # [(iso, location), ...] sorted by country, then location

if "smac_jurisdiction" not in st.session_state:
    st.session_state.smac_jurisdiction = ("USA", "California")

eyebrow("THE SMAC")
st.markdown(
    "<h1 style='font-size:2.4rem;margin-bottom:6px;'>Jurisdictions</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="smac-meta" style="margin-bottom:16px;">'
    'every button below is an actual SMAC member or observer &nbsp;·&nbsp; '
    'colored by country &nbsp;·&nbsp; A–Z by country, then by jurisdiction</div>',
    unsafe_allow_html=True,
)

# Build the per-button color/active-state CSS once, then render real st.button widgets
# inside st.container(key=...) wrappers — this is the supported way to give each
# button its own styling, since Streamlit renders every element as its own DOM node
# (raw HTML can't reach into a later widget's markup).
css_rules = []
for iso, loc in all_locs:
    slug = _slug(iso, loc)
    color = COUNTRY_COLORS.get(iso, "#0e9d6c")
    is_active = st.session_state.smac_jurisdiction == (iso, loc)
    ring = "outline:3px solid var(--ink); outline-offset:2px;" if is_active else ""
    css_rules.append(
        f'.st-key-{slug} button {{ background:{color} !important; color:#ffffff !important; '
        f'font-size:13px !important; padding:8px 14px !important; {ring} }}'
    )
    css_rules.append(f'.st-key-{slug} button:hover {{ filter:brightness(1.12); }}')
st.markdown(f"<style>{''.join(css_rules)}</style>", unsafe_allow_html=True)

PILLS_PER_ROW = 4
for row_start in range(0, len(all_locs), PILLS_PER_ROW):
    row_items = all_locs[row_start:row_start + PILLS_PER_ROW]
    cols = st.columns(PILLS_PER_ROW)
    for i, (iso, loc) in enumerate(row_items):
        with cols[i]:
            with st.container(key=_slug(iso, loc)):
                label = f"{display_name(loc)} ({COUNTRY_META[iso]['name']})"
                if st.button(label, key=f"btn-{_slug(iso, loc)}", use_container_width=True):
                    st.session_state.smac_jurisdiction = (iso, loc)
                    st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

iso, loc = st.session_state.smac_jurisdiction
loc_display = display_name(loc)
meta = COUNTRY_META[iso]
status = member_status(iso, loc)
status_label = {"member": "● SMAC Member", "observer": "○ SMAC Observer"}.get(status, "")

# ============== HEADER ==============
yearly = location_yearly(iso, loc)
y21 = float(yearly[yearly["year"] == 2021]["ch4_tonnes"].iloc[0]) if 2021 in yearly["year"].values else 0
y_prior = float(yearly[yearly["year"] == CURRENT_YEAR - 1]["ch4_tonnes"].iloc[0]) if (CURRENT_YEAR - 1) in yearly["year"].values else 0
y_now = float(yearly[yearly["year"] == CURRENT_YEAR]["ch4_tonnes"].iloc[0]) if CURRENT_YEAR in yearly["year"].values else 0
yoy = pct_change(y_now, y_prior)
drift = pct_change(y_now, y21)

ranking = location_yearly_ranking(iso, year=CURRENT_YEAR)
rank_row = ranking[ranking["location"] == loc]
rank_pos = (ranking.index[ranking["location"] == loc][0] + 1) if len(rank_row) else None
loc_share = float(rank_row["share"].iloc[0]) if len(rank_row) else None

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown(
        f'<div class="smac-meta" style="display:flex;align-items:center;gap:10px;">'
        f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
        f'background:{COUNTRY_COLORS.get(iso, "#0e9d6c")};"></span>'
        f'{meta["name"]} &nbsp;·&nbsp; {meta["region"]} &nbsp;·&nbsp; {DATA_RANGE_LABEL}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<h1 style='font-size:3.4rem;margin-top:8px;margin-bottom:6px;'>{loc_display}</h1>",
        unsafe_allow_html=True,
    )
    if status_label:
        st.markdown(f'<span class="smac-pill">{status_label}</span>', unsafe_allow_html=True)
    st.markdown(
        f'<a href="https://climatetrace.org/explore?search={loc.replace(" ", "+")}" '
        f'target="_blank" style="text-decoration:none;display:inline-block;margin-top:14px;">'
        f'<span class="smac-pill" style="background:var(--paper-3);color:var(--mint-deep);">'
        f'🗺 View {loc_display} source map on Climate TRACE →</span></a>',
        unsafe_allow_html=True,
    )
    with st.expander(f"Show map of {loc_display}"):
        import streamlit.components.v1 as components
        components.iframe(
            f"https://www.google.com/maps?q={loc.replace(' ', '+')}+{meta['name'].replace(' ', '+')}&output=embed",
            height=220,
        )

with col2:
    kpi_cols = st.columns(2)
    with kpi_cols[0]:
        yoy_is_nan = yoy != yoy
        st.metric(f"{CURRENT_YEAR} Total CH₄", f"{fmt_mt(y_now)} Mt",
                  "—" if yoy_is_nan else f"{yoy:+.2f}% YoY",
                  delta_color=("normal" if yoy_is_nan else ("inverse" if yoy > 0 else "normal")))
        st.metric("CO₂e · GWP100", f"{fmt_mt(y_now * GWP100)} Mt", f"×{GWP100} IPCC AR6", delta_color="off")
    with kpi_cols[1]:
        rank_label = f"#{rank_pos} of {len(ranking)} in {meta['name']}" if rank_pos else "—"
        st.metric("Rank within country", rank_label,
                  f"{loc_share:.1f}% of national CH₄" if loc_share is not None else "", delta_color="off")
        st.metric("CO₂e · GWP20", f"{fmt_mt(y_now * GWP20)} Mt", f"×{GWP20} IPCC AR6", delta_color="off")

st.markdown("<br>", unsafe_allow_html=True)

# ============== TIME SERIES + SECTOR BREAKDOWN ==============
col_a, col_b = st.columns([1.3, 1], gap="large")

with col_a:
    eyebrow("Monthly time series")
    st.markdown(f"<h3>CH₄ tonnes · {DATA_RANGE_LABEL}</h3>", unsafe_allow_html=True)
    monthly = location_monthly(iso, loc)
    st.plotly_chart(time_series_plotly(monthly, height=320), use_container_width=True,
                    config={"displayModeBar": False})

with col_b:
    eyebrow("Sector breakdown")
    st.markdown(f"<h3>{CURRENT_YEAR} · real Climate TRACE data</h3>", unsafe_allow_html=True)
    sec = location_sectors(iso, loc, CURRENT_YEAR)
    if sec.empty:
        st.info(f"No {CURRENT_YEAR} sector data for {loc_display} yet.")
    else:
        import plotly.graph_objects as go
        fig = go.Figure(go.Pie(
            labels=sec["sector"], values=sec["total_emission"], hole=0.5,
            marker=dict(colors=[SECTOR_COLORS.get(s, "#b9c4bd") for s in sec["sector"]]),
            textinfo="percent", textfont=dict(family="Quicksand, sans-serif", size=11),
        ))
        fig.update_layout(height=320, showlegend=True,
                          legend=dict(orientation="v", font=dict(size=10, family="Quicksand, sans-serif")),
                          margin=dict(l=0, r=0, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.markdown("<br>", unsafe_allow_html=True)

# ============== TOP EMISSION SOURCES + METHANE ACTION PLAN ==============
eyebrow("Top emission sources")
top_sectors = top_sectors_pareto(iso, loc, CURRENT_YEAR, threshold=0.80)

if top_sectors.empty:
    st.info(f"No {CURRENT_YEAR} data yet for {loc_display} to build an action plan from.")
else:
    st.markdown(
        f"<h3>The sectors driving ~{top_sectors['cum_share'].iloc[-1]*100:.0f}% of {loc_display}'s methane</h3>",
        unsafe_allow_html=True,
    )
    src_cols = st.columns(len(top_sectors))
    for i, row in enumerate(top_sectors.itertuples()):
        with src_cols[i]:
            st.markdown(
                f"""
                <div style="border:1px solid var(--line);border-left:4px solid {SECTOR_COLORS.get(row.sector, '#b9c4bd')};padding:16px 18px;background:var(--paper);height:100%;">
                  <div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:14px;margin-bottom:4px;">{row.sector}</div>
                  <div style="font-family:Quicksand,sans-serif;font-size:24px;font-weight:700;letter-spacing:-0.01em;">{row.share*100:.1f}%</div>
                  <div style="font-size:11px;color:var(--ink-soft);margin-top:2px;">{fmt_int(row.total_emission)} t CH₄</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    eyebrow("Methane Action Plan")
    st.markdown(f"<h3>Quick actions for {loc_display}, by top source</h3>", unsafe_allow_html=True)
    st.markdown(
        '<div class="smac-meta" style="margin-bottom:14px;">'
        'generic best-practice actions for each top sector — a starting checklist, not a '
        'substitute for a full jurisdiction-specific plan</div>',
        unsafe_allow_html=True,
    )
    bullets = action_plan_bullets(top_sectors)
    plan_cols = st.columns(2)
    for i, (sector, bullet) in enumerate(bullets):
        with plan_cols[i % 2]:
            st.markdown(
                f'<div style="display:flex;gap:10px;margin-bottom:12px;align-items:flex-start;">'
                f'<span style="width:8px;height:8px;border-radius:50%;background:{SECTOR_COLORS.get(sector, "#b9c4bd")};'
                f'flex-shrink:0;margin-top:6px;"></span>'
                f'<div><div style="font-family:Quicksand,sans-serif;font-size:10px;letter-spacing:0.08em;'
                f'text-transform:uppercase;color:var(--ink-soft);margin-bottom:2px;">{sector}</div>'
                f'<div style="font-size:13.5px;line-height:1.5;color:var(--ink);">{bullet}</div></div></div>',
                unsafe_allow_html=True,
            )

st.markdown("<br>", unsafe_allow_html=True)

# ============== COUNTRY POLICY CONTEXT ==============
policy = POLICY.get(iso, {})
if policy.get("policies"):
    eyebrow("Country policy context")
    st.markdown(f"<h3>{meta['name']}'s methane policy stack</h3>", unsafe_allow_html=True)
    st.markdown(
        f'<p style="font-size:14px;line-height:1.65;color:var(--ink-soft);margin-bottom:6px;">{policy.get("summary", "")}</p>'
        f'<p style="font-size:11px;line-height:1.5;color:var(--ink-soft);opacity:0.75;margin-bottom:16px;">'
        f'National-level context — this describes {meta["name"]}\'s policy landscape broadly, not {loc_display} specifically.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "".join(
            f'<p style="font-size:14px;line-height:1.65;color:var(--ink-soft);margin-bottom:12px;">'
            f'<strong style="color:var(--ink);">{n}.</strong> {d}</p>'
            for n, d in policy["policies"]
        ),
        unsafe_allow_html=True,
    )
