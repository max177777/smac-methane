"""
SMAC page — jurisdiction (not country) profile.
Every button is one actual SMAC member/observer subnational unit, color-coded by
country, sorted alphabetically by country then by jurisdiction. Shows that
jurisdiction's KPIs, time series, real sector breakdown, top emission sources, and a
quick-bullet Methane Action Plan built from those top sources.
"""

import re

import streamlit as st

from utils.theme import inject_theme, eyebrow, dark_band, render_footer
from utils.data_loader import (
    COUNTRY_META, COUNTRY_COLORS, CURRENT_YEAR, DATA_RANGE_LABEL,
    all_member_locations, member_status, location_yearly, location_monthly,
    smac_wide_ranking, location_sectors, top_sectors_pareto, action_plan_bullets,
    top_point_sources, fmt_int, fmt_mt, pct_change, display_name,
)
from utils.policy_content import POLICY, GWP100, GWP20, get_official_plans, get_climate_trace_detail_link
from utils.charts import time_series_plotly, SECTOR_COLORS, jurisdiction_map_plotly
from utils.rag import rag_search

inject_theme()


def _slug(iso: str, loc: str) -> str:
    return "jc-" + re.sub(r"[^a-z0-9]+", "-", f"{iso}-{loc}".lower()).strip("-")


# ============== ABOUT SMAC (mirrors smacmethane.org) ==============
hero_l, hero_r = st.columns([1.3, 1], gap="large")

with hero_l:
    eyebrow("Subnational Methane Action Coalition")
    st.markdown("<h1>Leading the world toward <em>fast methane action</em>.</h1>", unsafe_allow_html=True)
    st.markdown(
        '<p style="font-family:Inter,sans-serif;font-size:17px;line-height:1.65;'
        'color:var(--ink-soft);max-width:680px;margin-bottom:20px;">'
        "Worldwide, states and provinces have the authority and expertise to slash methane "
        "emissions and combat climate change. Members of the Subnational Methane Action "
        "Coalition (SMAC) are leading the way."
        "</p>",
        unsafe_allow_html=True,
    )

    btn_cols = st.columns([1, 1, 4])
    with btn_cols[0]:
        st.markdown(
            '<a href="https://www.smacmethane.org/benefits" target="_blank" style="text-decoration:none;">'
            '<span class="smac-pill" style="display:block;text-align:center;padding:10px 22px;font-size:15px;">Benefits</span></a>',
            unsafe_allow_html=True,
        )
    with btn_cols[1]:
        if st.button("Join", key="smac_join_btn", type="primary"):
            st.switch_page("pages/6_Contact.py")

    st.markdown(
        '<div style="margin-top:18px;margin-bottom:28px;">'
        '<a href="https://www.smacmethane.org/s/SMAC_Letter-from-California_2025-1-yg86.pdf" target="_blank" '
        'style="font-family:Quicksand,sans-serif;font-size:13px;font-weight:700;color:var(--mint-deep);text-decoration:none;">'
        '📄 An Invitation from California →</a></div>',
        unsafe_allow_html=True,
    )

    # ---- The Methane Imperative ---- (kept in the same column as the hero so
    # the map on the right can span the full combined height)
    eyebrow("The Methane Imperative")
    st.markdown(
        '<p style="font-family:Inter,sans-serif;font-size:15px;line-height:1.7;'
        'color:var(--ink-soft);max-width:720px;margin-bottom:14px;">'
        "Methane is a colorless, combustible gas that has caused nearly one-third of "
        "Earth's warming. In the short term, one ton of methane traps 80 times more heat "
        "than one ton of carbon dioxide. Since captured methane can be used for fuel, "
        "methane solutions are often profitable."
        "</p>"
        '<p style="font-family:Inter,sans-serif;font-size:15px;line-height:1.7;'
        'color:var(--ink-soft);max-width:720px;margin-bottom:8px;">'
        "States and provinces are uniquely positioned to lead the fight against methane "
        "emissions. SMAC provides a platform that helps governments gain access to "
        "technical and policy resources while learning from each other. Joining SMAC is "
        "always free."
        "</p>",
        unsafe_allow_html=True,
    )

with hero_r:
    st.markdown('<div style="height:48px;"></div>', unsafe_allow_html=True)
    st.plotly_chart(
        jurisdiction_map_plotly(height=500, show_legend=False),
        use_container_width=True,
        config={"displayModeBar": False},
    )

st.markdown(
    '<div style="border-top:1px solid var(--line);border-bottom:1px solid var(--line);'
    'padding:18px 0;margin:18px 0;display:flex;gap:48px;flex-wrap:wrap;">'
    '<div><div style="font-family:Quicksand,sans-serif;font-size:28px;font-weight:700;">375M+</div>'
    '<div class="smac-meta" style="font-size:11px;">combined population of SMAC members</div></div>'
    '<div><div style="font-family:Quicksand,sans-serif;font-size:28px;font-weight:700;">US$4.6T+</div>'
    '<div class="smac-meta" style="font-size:11px;">combined GDP of SMAC members</div></div>'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ---- Methane policy, simplified ----
with dark_band():
    eyebrow("What SMAC does")
    st.markdown("<h2 style='font-size:2.2rem;margin-bottom:8px;'>Methane policy, <em>simplified</em>.</h2>", unsafe_allow_html=True)
    st.markdown(
        '<p style="font-family:Inter,sans-serif;font-size:15px;line-height:1.65;'
        'color:rgba(255,255,255,0.75);max-width:680px;margin-bottom:28px;">'
        "Each jurisdiction has different needs. Whether a government is new to methane "
        "efforts or already a world leader, SMAC helps officials craft strong methane "
        "policies and gain global recognition for their efforts."
        "</p>",
        unsafe_allow_html=True,
    )
    smac_functions = [
        ("Identifying Solutions", "Through an extensive network of methane experts, SMAC helps governments build customized methane strategies to meet their needs."),
        ("Supporting Monitoring", "Through SMAC, governments identify key sources of methane, including through low-cost technologies and publicly available satellite data."),
        ("Deploying Projects", "Working alongside industry, SMAC tracks and facilitates innovative methane initiatives at oil and gas operations, farms, landfills, and other facilities."),
        ("Building Model Policies", "SMAC builds international collaborations to exchange model policies, laws, and rules."),
        ("Promoting Environmental Justice", "Through SMAC, governments are positioned to maximize the social, economic, and health benefits of methane action."),
    ]
    func_cols = st.columns(2)
    for i, (title, desc) in enumerate(smac_functions):
        with func_cols[i % 2]:
            st.markdown(
                f'<div style="display:flex;gap:12px;margin-bottom:22px;align-items:flex-start;">'
                f'<span style="width:9px;height:9px;border-radius:50%;background:var(--mint);flex-shrink:0;margin-top:7px;"></span>'
                f'<div><div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:15px;color:#ffffff;margin-bottom:4px;">{title}</div>'
                f'<div style="font-size:13px;line-height:1.55;color:rgba(255,255,255,0.72);">{desc}</div></div></div>',
                unsafe_allow_html=True,
            )

st.markdown("<br>", unsafe_allow_html=True)

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
        "Climate TRACE's public data for these jurisdictions doesn't include individual named "
        "facilities with coordinates — there's no point-source ID to rank. What it does have is "
        "a much finer breakdown than the 8 broad sectors above: 68 activity-level categories "
        "(e.g. \"oil-and-gas-production\", \"enteric-fermentation-cattle-operation\"). We treat "
        "each of those as one emitting source and rank them here — the closest faithful read on "
        "\"top sources\" the underlying data supports, tagged with its parent sector.</div>",
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

# ============== SATELLITE DATA (Climate TRACE detail page) ==============
eyebrow("Satellite data")
st.markdown(f"<h3>Observed plumes for {loc_display}</h3>", unsafe_allow_html=True)
st.markdown(
    '<div class="smac-meta" style="margin-bottom:14px;">'
    "the sources above are modeled from activity data; Climate TRACE's own detail page below "
    "shows satellite-observed air pollution directly — pairing the two shows where the "
    "inventory estimate and a direct observation agree, and where they don't</div>",
    unsafe_allow_html=True,
)

ct_detail_link = get_climate_trace_detail_link(iso, loc)
if ct_detail_link:
    import streamlit.components.v1 as components
    components.iframe(ct_detail_link, height=600)
    st.markdown(
        f'<div class="smac-meta" style="font-size:9px;margin:6px 0 0;line-height:1.5;">'
        f'if the panel above doesn\'t load, <a href="{ct_detail_link}" target="_blank" '
        f'style="color:var(--mint-deep);">open it directly on Climate TRACE →</a></div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f'<a href="https://climatetrace.org/air-pollution" target="_blank" style="text-decoration:none;">'
        f'<div class="smac-card" style="padding:16px 20px;">'
        f'<div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:14px;color:var(--ink);">'
        f'🛰️ Explore air pollution data on Climate TRACE →</div>'
        f'<div style="font-size:11.5px;color:var(--ink-soft);margin-top:2px;">'
        f'a {loc_display}-specific detail page isn\'t linked yet</div>'
        f'</div></a>',
        unsafe_allow_html=True,
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
