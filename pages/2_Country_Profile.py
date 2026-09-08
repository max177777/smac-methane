"""
SMAC Explorer — the data page.
Leads straight into jurisdiction selection: pick a SMAC member/observer and get
its KPIs, time series, sector breakdown, top emitting facilities, and a
Methane Action Plan. The "what is SMAC" material lives on the Overview page —
members coming here already know what SMAC is, they're here for their numbers.
"""

import re

import streamlit as st

from utils.theme import inject_theme, eyebrow, render_footer
from utils.data_loader import (
    COUNTRY_META, COUNTRY_COLORS, CURRENT_YEAR, DATA_RANGE_LABEL,
    all_member_locations, member_status, location_yearly, location_monthly,
    smac_wide_ranking, location_sectors, top_sectors_pareto, action_plan_bullets,
    top_point_sources, top_facility_sources, fmt_int, fmt_mt, pct_change, display_name,
)
from utils.policy_content import POLICY, GWP100, GWP20, get_official_plans
from utils.charts import time_series_plotly, SECTOR_COLORS
from utils.rag import rag_search

inject_theme()


def _slug(iso: str, loc: str) -> str:
    return "jc-" + re.sub(r"[^a-z0-9]+", "-", f"{iso}-{loc}".lower()).strip("-")



# ============== JURISDICTION SELECTOR ==============
all_locs = all_member_locations()  # [(iso, location), ...] sorted by country, then location

if "smac_jurisdiction" not in st.session_state:
    st.session_state.smac_jurisdiction = ("USA", "California")

eyebrow("Explore the data")
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
YEARS = list(range(2021, CURRENT_YEAR + 2))  # includes the partial current-year+1 (2026)
if "smac_year" not in st.session_state:
    st.session_state.smac_year = CURRENT_YEAR

yearly = location_yearly(iso, loc)
y21 = float(yearly[yearly["year"] == 2021]["ch4_tonnes"].iloc[0]) if 2021 in yearly["year"].values else 0

col1, col2 = st.columns([1, 1], gap="large")

with col2:
    sel_year = st.selectbox(
        "Year", options=list(reversed(YEARS)),
        index=YEARS[::-1].index(st.session_state.smac_year),
        key="smac_year_select",
    )
    st.session_state.smac_year = sel_year

y_prior = float(yearly[yearly["year"] == sel_year - 1]["ch4_tonnes"].iloc[0]) if (sel_year - 1) in yearly["year"].values else 0
y_now = float(yearly[yearly["year"] == sel_year]["ch4_tonnes"].iloc[0]) if sel_year in yearly["year"].values else 0
yoy = pct_change(y_now, y_prior)
drift = pct_change(y_now, y21)

smac_rank_df = smac_wide_ranking(sel_year)
smac_row = smac_rank_df[(smac_rank_df["iso3_country"] == iso) & (smac_rank_df["location"] == loc)]
smac_rank_pos = int(smac_row["rank"].iloc[0]) if len(smac_row) else None
smac_share = float(smac_row["share"].iloc[0]) if len(smac_row) else None
n_smac_jurisdictions = len(smac_rank_df)

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

with col2:
    # Hide only the little up/down arrow glyph on these three metrics (their delta
    # isn't a real increase/decrease, so an arrow is misleading) — targets each
    # metric's own st.container(key=...) so the delta TEXT stays visible and stays
    # inside the metric's card; only the SVG arrow icon is removed.
    st.markdown(
        """
        <style>
        .st-key-kpi-gwp100 [data-testid="stMetricDelta"] svg,
        .st-key-kpi-rank [data-testid="stMetricDelta"] svg,
        .st-key-kpi-gwp20 [data-testid="stMetricDelta"] svg {
          display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    kpi_cols = st.columns(2)
    with kpi_cols[0]:
        yoy_is_nan = yoy != yoy
        st.metric(
            f"{sel_year} Total CH₄", f"{fmt_mt(y_now)} Mt",
            "—" if yoy_is_nan else f"{yoy:+.2f}% YoY",
            delta_color=("normal" if yoy_is_nan else ("inverse" if yoy > 0 else "normal")),
            help=f"Total methane {loc_display} emitted in {sel_year}, in million tonnes (Mt). "
                 f"The small number below is the year-over-year change vs {sel_year - 1}.",
        )
        with st.container(key="kpi-gwp100"):
            st.metric(
                f"CO₂e · GWP100 · {sel_year}", f"{fmt_mt(y_now * GWP100)} Mt",
                f"×{GWP100} IPCC AR6", delta_color="off",
                help=f"{sel_year} methane converted to CO₂-equivalent using the 100-year Global "
                     f"Warming Potential (×{GWP100}) — the standard used in most national "
                     f"inventories and long-term climate accounting.",
            )
    with kpi_cols[1]:
        rank_label = f"#{smac_rank_pos} of {n_smac_jurisdictions}" if smac_rank_pos else "—"
        with st.container(key="kpi-rank"):
            st.metric(
                f"Rank within SMAC · {sel_year}", rank_label,
                f"{smac_share:.1f}% of all SMAC CH₄" if smac_share is not None else "", delta_color="off",
                help=f"{loc_display}'s position when every one of the {n_smac_jurisdictions} SMAC "
                     f"member/observer jurisdictions worldwide is ranked by {sel_year} methane "
                     f"emissions, #1 = highest. The percentage is {loc_display}'s share of the "
                     f"combined total that all {n_smac_jurisdictions} SMAC jurisdictions emitted "
                     f"together in {sel_year} — e.g. \"7.3%\" means this one jurisdiction accounts "
                     f"for 7.3% of everything the whole SMAC coalition emitted that year.",
            )
        with st.container(key="kpi-gwp20"):
            st.metric(
                f"CO₂e · GWP20 · {sel_year}", f"{fmt_mt(y_now * GWP20)} Mt",
                f"×{GWP20} IPCC AR6", delta_color="off",
                help=f"{sel_year} methane converted to CO₂-equivalent using the 20-year Global "
                     f"Warming Potential (×{GWP20}) — reflects methane's much stronger near-term "
                     f"warming effect, relevant for near-term (e.g. 2030/2050) climate targets.",
            )

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
    st.markdown(f"<h3>{sel_year} · real Climate TRACE data</h3>", unsafe_allow_html=True)
    sec = location_sectors(iso, loc, sel_year)
    if sec.empty:
        st.info(f"No {sel_year} sector data for {loc_display} yet.")
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

# ============== TOP 20 EMITTING SOURCES ==============
eyebrow("Top emitting sources")

# Prefer real named facilities (individual landfills, oil & gas sites) when
# scripts/fetch_point_sources.py has been run and its CSV committed. Fall back
# to the sub-sector ranking when it hasn't.
facilities = top_facility_sources(iso, loc, sel_year, top_n=20)

if not facilities.empty:
    top_n_share = facilities.attrs.get("top_n_share_pct", 0.0)
    st.markdown(
        f"<h3>Top {len(facilities)} facilities ≈ <em>{top_n_share:.1f}%</em> of "
        f"{loc_display}'s {sel_year} facility-level methane</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="smac-meta" style="margin-bottom:14px;">'
        "individual emitting assets from Climate TRACE, ranked by methane. Waste, power, "
        "manufacturing and mineral-extraction rows are genuine single sites (a named landfill, "
        "a named plant). <strong>Oil &amp; gas rows are often field- or basin-level aggregates</strong> "
        "rather than one wellpad — e.g. an entry covering a whole production play — so treat "
        "those as \"where to look\" rather than \"which gate to knock on\". Road transport, "
        "forestry and most agriculture are excluded entirely, because there an emissions "
        "source is a road segment or grid cell, not a site.</div>",
        unsafe_allow_html=True,
    )
    fac_cols = {
        "source_name": "Facility", "asset_type": "Type", "sector": "Sector",
        "sub_sector": "Sub-sector",
        "ch4_tonnes": f"{sel_year} CH₄ (t)", "share": "Share of facility total (%)",
    }
    show_cols = {k: v for k, v in fac_cols.items() if k in facilities.columns}
    display_fac = facilities[list(show_cols)].rename(columns=show_cols)
    st.dataframe(
        display_fac, hide_index=True, use_container_width=True, height=460,
        column_config={
            "Facility": st.column_config.TextColumn(width="medium"),
            "Type": st.column_config.TextColumn(width="small"),
            "Sector": st.column_config.TextColumn(width="small"),
            "Sub-sector": st.column_config.TextColumn(width="small"),
            f"{sel_year} CH₄ (t)": st.column_config.NumberColumn(format="%d"),
            "Share of facility total (%)": st.column_config.ProgressColumn(
                format="%.2f%%", min_value=0,
                max_value=float(display_fac["Share of facility total (%)"].max())
                if "Share of facility total (%)" in display_fac else 1.0,
            ),
        },
    )
    if {"lat", "lon"}.issubset(facilities.columns):
        pts = facilities.dropna(subset=["lat", "lon"])
        if not pts.empty:
            st.markdown(
                '<div class="smac-meta" style="margin-top:10px;">facility locations</div>',
                unsafe_allow_html=True,
            )
            st.map(pts.rename(columns={"lat": "latitude", "lon": "longitude"})[
                ["latitude", "longitude"]], size=400)

else:
    top20 = top_point_sources(iso, loc, sel_year, top_n=20)
    if top20.empty:
        st.info(f"No {sel_year} source-level data yet for {loc_display}.")
    else:
        top_n_share = top20.attrs.get("top_n_share_pct", 0.0)
        st.markdown(
            f"<h3>Top {len(top20)} sources ≈ <em>{top_n_share:.1f}%</em> of {loc_display}'s {sel_year} methane</h3>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="smac-meta" style="margin-bottom:14px;">'
            "these are activity-level categories, not individual facilities. Facility-level data "
            "for this jurisdiction hasn't been loaded yet — run "
            "<code>scripts/fetch_point_sources.py</code> to pull named sites from Climate TRACE's "
            "asset API. Until then, this ranks the 68 activity categories (e.g. "
            "\"oil-and-gas-production\") that the aggregated dataset does cover.</div>",
            unsafe_allow_html=True,
        )
        display_top20 = top20[["sub_sector_label", "sector", "total_emission", "share"]].rename(columns={
            "sub_sector_label": "Emitting source", "sector": "Sector",
            "total_emission": f"{sel_year} CH₄ (t)", "share": "Share of jurisdiction (%)",
        })
        st.dataframe(
            display_top20, hide_index=True, use_container_width=True, height=460,
            column_config={
                "Emitting source": st.column_config.TextColumn(width="medium"),
                "Sector": st.column_config.TextColumn(width="medium"),
                f"{sel_year} CH₄ (t)": st.column_config.NumberColumn(format="%d"),
                "Share of jurisdiction (%)": st.column_config.ProgressColumn(
                    format="%.2f%%", min_value=0, max_value=float(display_top20["Share of jurisdiction (%)"].max()),
                ),
            },
        )

st.markdown("<br>", unsafe_allow_html=True)


# ============== TOP SECTORS + METHANE ACTION PLAN ==============
eyebrow("Top sectors")
top_sectors = top_sectors_pareto(iso, loc, sel_year, threshold=0.80)

if top_sectors.empty:
    st.info(f"No {sel_year} data yet for {loc_display} to build an action plan from.")
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

    official_plans = get_official_plans(iso, loc)
    rag_hits = rag_search(
        f"methane action plan mitigation strategy for {loc_display}",
        iso=iso, location=loc, output_type="pathway", k=4,
    )
    dedicated_hits = [h for h in rag_hits if h["location"] == loc]
    has_dedicated = bool(official_plans) or bool(dedicated_hits)

    if has_dedicated:
        st.markdown(f"<h3>{loc_display}'s actual methane action plan</h3>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h3>Quick actions for {loc_display}, by top source</h3>", unsafe_allow_html=True)

    if official_plans:
        st.markdown(
            '<div class="smac-meta" style="margin-bottom:10px;">official external plan(s) on file</div>',
            unsafe_allow_html=True,
        )
        for p in official_plans:
            st.markdown(
                f'<a href="{p["url"]}" target="_blank" style="text-decoration:none;display:block;margin-bottom:10px;">'
                f'<div class="smac-card" style="padding:14px 18px;">'
                f'<div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:14px;color:var(--ink);">📄 {p["title"]} →</div>'
                f'<div style="font-size:11.5px;color:var(--ink-soft);margin-top:2px;">{p["org"]} · {p["year"]}</div>'
                f'</div></a>',
                unsafe_allow_html=True,
            )

    if dedicated_hits:
        st.markdown(
            '<div class="smac-meta" style="margin:14px 0 10px;">'
            f'excerpts retrieved from {loc_display}\'s own documents in our library</div>',
            unsafe_allow_html=True,
        )
        for h in dedicated_hits[:3]:
            st.markdown(
                f'<div class="smac-card" style="padding:14px 18px;margin-bottom:10px;">'
                f'<div style="font-size:13px;line-height:1.55;color:var(--ink);margin-bottom:6px;">'
                f'&ldquo;{h["text"][:400]}{"…" if len(h["text"]) > 400 else ""}&rdquo;</div>'
                f'<div class="smac-meta" style="font-size:10.5px;">source: {h["source_file"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    if not has_dedicated:
        st.markdown(
            '<div class="smac-meta" style="margin-bottom:14px;">'
            f'no dedicated action plan indexed for {loc_display} yet — showing generic '
            'best-practice actions for each top sector instead, plus the closest matches '
            'from our general solution-bank library</div>',
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
        if rag_hits:
            st.markdown(
                '<div class="smac-meta" style="margin:14px 0 10px;">'
                'closest matches from the general solution-bank library</div>',
                unsafe_allow_html=True,
            )
            for h in rag_hits[:2]:
                st.markdown(
                    f'<div class="smac-card" style="padding:14px 18px;margin-bottom:10px;">'
                    f'<div style="font-size:13px;line-height:1.55;color:var(--ink);margin-bottom:6px;">'
                    f'&ldquo;{h["text"][:350]}{"…" if len(h["text"]) > 350 else ""}&rdquo;</div>'
                    f'<div class="smac-meta" style="font-size:10.5px;">source: {h["source_file"]}</div>'
                    f'</div>',
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


render_footer()
