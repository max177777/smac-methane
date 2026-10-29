"""
SMAC Explorer — the data page.
Leads straight into jurisdiction selection: pick a SMAC member/observer and get
its KPIs, time series, sector breakdown, top emitting facilities, and a
existing action plans. The "what is SMAC" material lives on the Overview page —
members coming here already know what SMAC is, they're here for their numbers.
"""

import re

import streamlit as st

from utils.theme import inject_theme, eyebrow, render_footer
from utils.data_loader import (
    COUNTRY_META, COUNTRY_COLORS, CURRENT_YEAR, DATA_RANGE_LABEL,
    CT_SNAPSHOT_DATE, CT_API_VERSION, under_construction_note, snapshot_for,
    all_member_locations, member_status, location_yearly, location_monthly,
    smac_wide_ranking, location_sectors, top_sectors_pareto, action_plan_bullets,
    location_yoy_like_for_like, has_location_data, location_subsectors, SECTOR_ORDER,
    top_point_sources, top_facility_sources, fmt_int, fmt_mt, pct_change, display_name,
)
from utils.policy_content import POLICY, GWP100, GWP20, get_official_plans
from utils.charts import time_series_plotly, SECTOR_COLORS
from utils.rag import rag_search
from utils.data_loader import SECTOR_ACTIONS
from utils.i18n import t, tk, sector_name, subsector_name, country_name, region_name

inject_theme()


def _slug(iso: str, loc: str) -> str:
    return "jc-" + re.sub(r"[^a-z0-9]+", "-", f"{iso}-{loc}".lower()).strip("-")



# ============== JURISDICTION SELECTOR ==============
all_locs = all_member_locations()  # [(iso, location), ...] sorted by country, then location

if "smac_jurisdiction" not in st.session_state:
    st.session_state.smac_jurisdiction = ("USA", "Maryland")

eyebrow(t("profile.eyebrow"))
st.markdown(
    f"<h1 style='font-size:2.4rem;margin-bottom:6px;'>{t('profile.title')}</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="smac-meta" style="margin-bottom:6px;">{t("profile.picker_note")}</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="smac-meta" style="font-size:10px;margin-bottom:16px;opacity:0.8;">'
    f'{t("common.ct_snapshot", date=CT_SNAPSHOT_DATE, api=CT_API_VERSION)}</div>',
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
                label = f"{display_name(loc)} ({country_name(iso)})"
                if st.button(label, key=f"btn-{_slug(iso, loc)}", use_container_width=True):
                    st.session_state.smac_jurisdiction = (iso, loc)
                    st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

iso, loc = st.session_state.smac_jurisdiction
loc_display = display_name(loc)
meta = COUNTRY_META[iso]
status = member_status(iso, loc)
status_label = {"member": t("common.smac_member_pill"),
                "observer": t("common.smac_observer_pill")}.get(status, "")

# ============== UNDER CONSTRUCTION GATE ==============
# Some jurisdictions maintain their own detailed inventory. Until that's
# reconciled against Climate TRACE, showing the Climate TRACE figure alone
# would present one of two disagreeing answers as if it were settled.
_uc = under_construction_note(iso, loc)
if _uc:
    st.markdown(
        f'<div class="smac-meta" style="display:flex;align-items:center;gap:10px;">'
        f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
        f'background:{COUNTRY_COLORS.get(iso, "#0e9d6c")};"></span>'
        f'{country_name(iso)} &nbsp;·&nbsp; {region_name(meta["region"])}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<h1 style='font-size:3.4rem;margin-top:8px;margin-bottom:6px;'>{loc_display}</h1>",
        unsafe_allow_html=True,
    )
    if status_label:
        st.markdown(f'<span class="smac-pill">{status_label}</span>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f'<div class="smac-card" style="padding:26px 30px;border-left:4px solid var(--copper);'
        f'max-width:780px;">'
        f'<div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:16px;'
        f'margin-bottom:8px;">🚧 {t("profile.uc_title")}</div>'
        f'<p style="font-size:14.5px;line-height:1.7;color:var(--ink-soft);margin-bottom:12px;">'
        f'{tk(f"uc.{iso}.{loc}", _uc)}</p>'
        f'<p style="font-size:13px;line-height:1.7;color:var(--ink-soft);margin:0;">'
        f'{t("profile.uc_body", loc=loc_display)}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div class="smac-meta">{t("profile.uc_contact")}</div>', unsafe_allow_html=True)
    if st.button(t("common.go_contact"), key="uc_contact"):
        st.switch_page("pages/6_Contact.py")
    render_footer()
    st.stop()

# ============== DATA PENDING GATE ==============
# A newly joined member is on the roster before its Climate TRACE rows are
# merged in (scripts/add_jurisdiction.py). Without this, every KPI below would
# render as 0.00 Mt — which reads as a real (and absurd) figure, not a gap.
if not has_location_data(iso, loc):
    st.markdown(
        f'<div class="smac-meta" style="display:flex;align-items:center;gap:10px;">'
        f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
        f'background:{COUNTRY_COLORS.get(iso, "#0e9d6c")};"></span>'
        f'{country_name(iso)} &nbsp;·&nbsp; {region_name(meta["region"])}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<h1 style='font-size:3.4rem;margin-top:8px;margin-bottom:6px;'>{loc_display}</h1>",
        unsafe_allow_html=True,
    )
    if status_label:
        st.markdown(f'<span class="smac-pill">{status_label}</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f'<div class="smac-card" style="padding:26px 30px;border-left:4px solid var(--mint);'
        f'max-width:780px;">'
        f'<div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:16px;'
        f'margin-bottom:8px;">{t("profile.pending_title")}</div>'
        f'<p style="font-size:14.5px;line-height:1.7;color:var(--ink-soft);margin:0;">'
        f'{t("profile.pending_body", loc=loc_display, date=CT_SNAPSHOT_DATE)}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    render_footer()
    st.stop()

# ============== HEADER ==============
YEARS = list(range(2021, CURRENT_YEAR + 2))  # includes the partial current-year+1 (2026)
if "smac_year" not in st.session_state:
    st.session_state.smac_year = CURRENT_YEAR

yearly = location_yearly(iso, loc)
y21 = float(yearly[yearly["year"] == 2021]["ch4_tonnes"].iloc[0]) if 2021 in yearly["year"].values else 0

col1, col2 = st.columns([1, 1], gap="large")

with col2:
    sel_year = st.selectbox(
        t("common.year"), options=list(reversed(YEARS)),
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
        f'{country_name(iso)} &nbsp;·&nbsp; {region_name(meta["region"])} &nbsp;·&nbsp; {DATA_RANGE_LABEL}</div>',
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
        f'🗺 {t("profile.ct_map", loc=loc_display)} →</span></a>',
        unsafe_allow_html=True,
    )
    _snap_loc = snapshot_for(iso, loc)
    if _snap_loc != CT_SNAPSHOT_DATE:
        st.markdown(
            f'<div class="smac-meta" style="font-size:10px;margin-top:10px;max-width:460px;">'
            f'{t("profile.kept_snapshot", loc=loc_display, old=_snap_loc, new=CT_SNAPSHOT_DATE)}</div>',
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
        # A partial year (2026 currently holds 5 months) compared against a full
        # 12-month prior year reads as a ~58% collapse that is purely a
        # reporting-window artefact — for Maryland the like-for-like change is
        # actually +0.7%. So for partial years we compare the same months only,
        # and label the card as year-to-date rather than a full-year total.
        _lfl = location_yoy_like_for_like(iso, loc, sel_year)
        _partial = _lfl["is_partial"]
        _yoy = _lfl["yoy_pct"] if _partial else yoy
        _yoy_is_nan = _yoy != _yoy
        _n_mo = _lfl["n_months"]

        _label = (t("profile.kpi_partial", y=sel_year, n=_n_mo) if _partial
                  else t("profile.kpi_total", y=sel_year))
        _delta = ("—" if _yoy_is_nan else
                  (t("profile.delta_partial", pct=f"{_yoy:+.2f}", n=_n_mo, py=sel_year - 1)
                   if _partial else t("profile.delta_yoy", pct=f"{_yoy:+.2f}")))
        _help = (t("profile.help_partial", loc=loc_display, n=_n_mo, y=sel_year, py=sel_year - 1)
                 if _partial else t("profile.help_total", loc=loc_display, y=sel_year, py=sel_year - 1))
        st.metric(
            _label, f"{fmt_mt(y_now)} Mt", _delta,
            delta_color=("normal" if _yoy_is_nan else ("inverse" if _yoy > 0 else "normal")),
            help=_help,
        )
        if _partial:
            st.markdown(
                f'<div class="smac-meta" style="font-size:10px;margin:-10px 0 12px;">'
                f'{t("common.partial_year_warn", y=sel_year, n=_n_mo)}</div>',
                unsafe_allow_html=True,
            )
        with st.container(key="kpi-gwp100"):
            st.metric(
                t("common.gwp100_label", y=sel_year), f"{fmt_mt(y_now * GWP100)} Mt",
                t("common.ipcc_factor", f=GWP100), delta_color="off",
                help=t("profile.help_gwp100", y=sel_year, f=GWP100),
            )
    with kpi_cols[1]:
        rank_label = (t("profile.rank_of", pos=smac_rank_pos, n=n_smac_jurisdictions)
                      if smac_rank_pos else "—")
        with st.container(key="kpi-rank"):
            st.metric(
                t("profile.rank_label", y=sel_year), rank_label,
                t("profile.rank_share", pct=f"{smac_share:.1f}") if smac_share is not None else "",
                delta_color="off",
                help=t("profile.help_rank", loc=loc_display, n=n_smac_jurisdictions, y=sel_year),
            )
        with st.container(key="kpi-gwp20"):
            st.metric(
                t("common.gwp20_label", y=sel_year), f"{fmt_mt(y_now * GWP20)} Mt",
                t("common.ipcc_factor", f=GWP20), delta_color="off",
                help=t("profile.help_gwp20", y=sel_year, f=GWP20),
            )

st.markdown("<br>", unsafe_allow_html=True)

# ============== TIME SERIES + SECTOR BREAKDOWN ==============
col_a, col_b = st.columns([1.3, 1], gap="large")

with col_a:
    eyebrow(t("common.monthly_series"))
    st.markdown(f"<h3>{t('common.ch4_tonnes')} · {DATA_RANGE_LABEL}</h3>", unsafe_allow_html=True)
    monthly = location_monthly(iso, loc)
    st.plotly_chart(time_series_plotly(monthly, height=320), use_container_width=True,
                    config={"displayModeBar": False})

with col_b:
    eyebrow(t("common.sector_breakdown"))
    st.markdown(f"<h3>{t('profile.sector_h3', y=sel_year)}</h3>", unsafe_allow_html=True)
    sec = location_sectors(iso, loc, sel_year)
    if sec.empty:
        st.info(t("profile.no_sector", y=sel_year, loc=loc_display))
    else:
        import plotly.graph_objects as go
        fig = go.Figure(go.Pie(
            labels=[sector_name(x) for x in sec["sector"]], values=sec["total_emission"], hole=0.5,
            marker=dict(colors=[SECTOR_COLORS.get(s, "#b9c4bd") for s in sec["sector"]]),
            textinfo="percent", textfont=dict(family="Quicksand, sans-serif", size=11),
        ))
        fig.update_layout(height=320, showlegend=True,
                          legend=dict(orientation="v", font=dict(size=10, family="Quicksand, sans-serif")),
                          margin=dict(l=0, r=0, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.markdown("<br>", unsafe_allow_html=True)

# ============== SECTOR DRILL-DOWN ==============
# Requested by Jalisco: the 8 broad categories hide the split that matters
# for policy inside a sector — above all, how much of Agriculture is enteric
# fermentation (and on pasture vs. in cattle operations) versus manure or rice.
# Built from the 68 Climate TRACE sub-sectors already in SMAC_ch4_subsectors.csv.
if not sec.empty:
    eyebrow(t("profile.drill_eyebrow"))
    _present = [s for s in SECTOR_ORDER
                if s in set(sec.loc[sec["total_emission"] > 0, "sector"])]
    _default = "Agriculture" if "Agriculture" in _present else (_present[0] if _present else None)
    if _default:
        dd_l, dd_r = st.columns([1, 2.2], gap="large")
        with dd_l:
            dd_sector = st.selectbox(
                t("profile.drill_select"), options=_present, format_func=sector_name,
                index=_present.index(_default), key="smac_drill_sector",
            )
        sub_df = location_subsectors(iso, loc, dd_sector, sel_year)
        with dd_l:
            if not sub_df.empty:
                sec_total = float(sub_df["total_emission"].sum())
                sec_share = float(sub_df["share_of_total"].sum())
                st.markdown(
                    f'<div style="font-family:Quicksand,sans-serif;font-size:26px;font-weight:700;'
                    f'margin-top:6px;">{fmt_int(sec_total)} t</div>'
                    f'<div class="smac-meta" style="font-size:11px;">'
                    f'{t("profile.drill_total", sector=sector_name(dd_sector), y=sel_year, pct=f"{sec_share:.1f}", loc=loc_display)}</div>',
                    unsafe_allow_html=True,
                )
                if dd_sector == "Agriculture":
                    ent = sub_df[sub_df["sub_sector"].str.startswith("enteric-fermentation")]
                    if not ent.empty:
                        _ent_pct = f'{ent["share_of_total"].sum():.1f}'
                        st.markdown(
                            f'<div class="smac-card" style="padding:14px 16px;margin-top:14px;">'
                            f'<div class="smac-meta" style="font-size:10px;">{t("profile.enteric")}</div>'
                            f'<div style="font-family:Quicksand,sans-serif;font-size:22px;font-weight:700;">'
                            f'{ent["share_of_sector"].sum():.1f}% <span style="font-size:12px;font-weight:400;'
                            f'color:var(--ink-soft);">{t("profile.of_agriculture")}</span></div>'
                            f'<div style="font-size:11.5px;color:var(--ink-soft);margin-top:2px;">'
                            f'{fmt_int(ent["total_emission"].sum())} t CH₄ · '
                            f'{t("profile.of_all_methane", pct=_ent_pct, loc=loc_display)}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
        with dd_r:
            st.markdown(f"<h3>{t('profile.drill_h3', sector=sector_name(dd_sector), y=sel_year)}</h3>",
                        unsafe_allow_html=True)
            if sub_df.empty:
                st.info(t("profile.drill_none", y=sel_year, sector=sector_name(dd_sector), loc=loc_display))
            else:
                import plotly.graph_objects as go
                _d = sub_df.sort_values("total_emission", ascending=True)
                _fig = go.Figure(go.Bar(
                    x=_d["total_emission"], y=[subsector_name(x) for x in _d["sub_sector"]], orientation="h",
                    marker_color=SECTOR_COLORS.get(dd_sector, "#b9c4bd"),
                    customdata=_d[["share_of_sector", "share_of_total"]].values,
                    hovertemplate="<b>%{y}</b><br>%{x:,.0f} t CH₄<br>"
                                  + t("profile.drill_hover") +
                                  "<extra></extra>",
                ))
                _fig.update_layout(
                    height=max(180, 34 * len(_d) + 50), margin=dict(l=0, r=10, t=6, b=10),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(title="CH₄ (t)", tickformat=",.0f", gridcolor="#e2e9e5",
                               tickfont=dict(size=10, family="Quicksand, sans-serif")),
                    yaxis=dict(tickfont=dict(size=11, family="Inter, sans-serif")),
                    font=dict(family="Inter, sans-serif"),
                )
                st.plotly_chart(_fig, use_container_width=True, config={"displayModeBar": False})
                st.markdown(
                    f'<div class="smac-meta" style="font-size:10px;">{t("profile.drill_note")}</div>',
                    unsafe_allow_html=True,
                )
    st.markdown("<br>", unsafe_allow_html=True)

# ============== TOP 20 EMITTING SOURCES ==============
eyebrow(t("common.top_sources"))

# Prefer real named facilities (individual landfills, oil & gas sites) when
# scripts/fetch_point_sources.py has been run and its CSV committed. Fall back
# to the sub-sector ranking when it hasn't.
facilities = top_facility_sources(iso, loc, sel_year, top_n=20)

if not facilities.empty:
    top_n_share = facilities.attrs.get("top_n_share_pct", 0.0)
    st.markdown(
        f"<h3>{t('profile.fac_h3', n=len(facilities), pct=f'{top_n_share:.1f}', loc=loc_display, y=sel_year)}</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="smac-meta" style="margin-bottom:14px;">{t("profile.fac_note")}</div>',
        unsafe_allow_html=True,
    )
    _c_fac, _c_type, _c_sec, _c_sub = (t("common.facility"), t("common.type"),
                                       t("common.sector"), t("common.subsector"))
    _c_ch4, _c_share = t("common.ch4_t_col", y=sel_year), t("profile.share_fac_col")
    fac_cols = {
        "source_name": _c_fac, "asset_type": _c_type, "sector": _c_sec,
        "sub_sector": _c_sub, "ch4_tonnes": _c_ch4, "share": _c_share,
    }
    show_cols = {k: v for k, v in fac_cols.items() if k in facilities.columns}
    display_fac = facilities[list(show_cols)].rename(columns=show_cols)
    st.dataframe(
        display_fac, hide_index=True, use_container_width=True, height=460,
        column_config={
            _c_fac: st.column_config.TextColumn(width="medium"),
            _c_type: st.column_config.TextColumn(width="small"),
            _c_sec: st.column_config.TextColumn(width="small"),
            _c_sub: st.column_config.TextColumn(width="small"),
            _c_ch4: st.column_config.NumberColumn(format="localized"),
            _c_share: st.column_config.ProgressColumn(
                format="%.2f%%", min_value=0,
                max_value=float(display_fac[_c_share].max()) if _c_share in display_fac else 1.0,
            ),
        },
    )
    if {"lat", "lon"}.issubset(facilities.columns):
        pts = facilities.dropna(subset=["lat", "lon"])
        if not pts.empty:
            st.markdown(
                f'<div class="smac-meta" style="margin-top:10px;">{t("common.facility_locations")}</div>',
                unsafe_allow_html=True,
            )
            st.map(pts.rename(columns={"lat": "latitude", "lon": "longitude"})[
                ["latitude", "longitude"]], size=400)

else:
    top20 = top_point_sources(iso, loc, sel_year, top_n=20)
    if top20.empty:
        st.info(t("profile.no_sources", y=sel_year, loc=loc_display))
    else:
        top_n_share = top20.attrs.get("top_n_share_pct", 0.0)
        st.markdown(
            f"<h3>{t('profile.src_h3', n=len(top20), pct=f'{top_n_share:.1f}', loc=loc_display, y=sel_year)}</h3>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="smac-meta" style="margin-bottom:14px;">{t("profile.src_note")}</div>',
            unsafe_allow_html=True,
        )
        _s_src, _s_sec = t("profile.src_col"), t("common.sector")
        _s_ch4, _s_share = t("common.ch4_t_col", y=sel_year), t("profile.share_juris_col")
        display_top20 = top20[["sub_sector", "sector", "total_emission", "share"]].copy()
        display_top20["sub_sector"] = display_top20["sub_sector"].map(subsector_name)
        display_top20["sector"] = display_top20["sector"].map(sector_name)
        display_top20 = display_top20.rename(columns={
            "sub_sector": _s_src, "sector": _s_sec, "total_emission": _s_ch4, "share": _s_share,
        })
        st.dataframe(
            display_top20, hide_index=True, use_container_width=True, height=460,
            column_config={
                _s_src: st.column_config.TextColumn(width="medium"),
                _s_sec: st.column_config.TextColumn(width="medium"),
                _s_ch4: st.column_config.NumberColumn(format="localized"),
                _s_share: st.column_config.ProgressColumn(
                    format="%.2f%%", min_value=0, max_value=float(display_top20[_s_share].max()),
                ),
            },
        )

st.markdown("<br>", unsafe_allow_html=True)


# ============== TOP SECTORS + METHANE ACTION PLAN ==============
eyebrow(t("profile.top_sectors"))
top_sectors = top_sectors_pareto(iso, loc, sel_year, threshold=0.80)

if top_sectors.empty:
    st.info(t("profile.no_plan_data", y=sel_year, loc=loc_display))
else:
    _pareto_pct = f"{top_sectors['cum_share'].iloc[-1] * 100:.0f}"
    st.markdown(
        f"<h3>{t('profile.pareto_h3', pct=_pareto_pct, loc=loc_display)}</h3>",
        unsafe_allow_html=True,
    )
    src_cols = st.columns(len(top_sectors))
    for i, row in enumerate(top_sectors.itertuples()):
        with src_cols[i]:
            st.markdown(
                f"""
                <div style="border:1px solid var(--line);border-left:4px solid {SECTOR_COLORS.get(row.sector, '#b9c4bd')};padding:16px 18px;background:var(--paper);height:100%;">
                  <div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:14px;margin-bottom:4px;">{sector_name(row.sector)}</div>
                  <div style="font-family:Quicksand,sans-serif;font-size:24px;font-weight:700;letter-spacing:-0.01em;">{row.share*100:.1f}%</div>
                  <div style="font-size:11px;color:var(--ink-soft);margin-top:2px;">{fmt_int(row.total_emission)} t CH₄</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    official_plans = get_official_plans(iso, loc)
    rag_hits = rag_search(
        f"methane action plan mitigation strategy for {loc_display}",
        iso=iso, location=loc, output_type="pathway", k=4,
    )
    dedicated_hits = [h for h in rag_hits if h["location"] == loc]
    has_dedicated = bool(official_plans) or bool(dedicated_hits)

    # Wording follows what is actually on file. The old "Methane Action Plan"
    # label implied SMAC had produced a plan for every jurisdiction, and the
    # "actual methane action plan" heading overstated documents that are often
    # broader climate plans (e.g. Maryland's CCAP, Jalisco's PEACC).
    if official_plans:
        eyebrow(t("profile.plans_eyebrow"))
        st.markdown(f"<h3>{t('profile.plans_h3', loc=loc_display)}</h3>", unsafe_allow_html=True)
    elif dedicated_hits:
        eyebrow(t("profile.docs_eyebrow"))
        st.markdown(f"<h3>{t('profile.docs_h3', loc=loc_display)}</h3>", unsafe_allow_html=True)
    else:
        eyebrow(t("profile.suggest_eyebrow"))
        st.markdown(f"<h3>{t('profile.suggest_h3', loc=loc_display)}</h3>", unsafe_allow_html=True)

    if official_plans:
        st.markdown(
            f'<div class="smac-meta" style="margin-bottom:10px;">{t("profile.plans_note")}</div>',
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
            f'{t("profile.docs_note", loc=loc_display)}</div>',
            unsafe_allow_html=True,
        )
        for h in dedicated_hits[:3]:
            st.markdown(
                f'<div class="smac-card" style="padding:14px 18px;margin-bottom:10px;">'
                f'<div style="font-size:13px;line-height:1.55;color:var(--ink);margin-bottom:6px;">'
                f'&ldquo;{h["text"][:400]}{"…" if len(h["text"]) > 400 else ""}&rdquo;</div>'
                f'<div class="smac-meta" style="font-size:10.5px;">{t("profile.source")}: {h["source_file"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    if not has_dedicated:
        st.markdown(
            '<div class="smac-meta" style="margin-bottom:14px;">'
            f'{t("profile.suggest_note", loc=loc_display)}</div>',
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
                    f'text-transform:uppercase;color:var(--ink-soft);margin-bottom:2px;">{sector_name(sector)}</div>'
                    f'<div style="font-size:13.5px;line-height:1.5;color:var(--ink);">'
                    f'{tk(f"action.{sector}.{SECTOR_ACTIONS[sector].index(bullet)}", bullet)}</div></div></div>',
                    unsafe_allow_html=True,
                )
        if rag_hits:
            st.markdown(
                '<div class="smac-meta" style="margin:14px 0 10px;">'
                f'{t("profile.bank_note")}</div>',
                unsafe_allow_html=True,
            )
            for h in rag_hits[:2]:
                st.markdown(
                    f'<div class="smac-card" style="padding:14px 18px;margin-bottom:10px;">'
                    f'<div style="font-size:13px;line-height:1.55;color:var(--ink);margin-bottom:6px;">'
                    f'&ldquo;{h["text"][:350]}{"…" if len(h["text"]) > 350 else ""}&rdquo;</div>'
                    f'<div class="smac-meta" style="font-size:10.5px;">{t("profile.source")}: {h["source_file"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

st.markdown("<br>", unsafe_allow_html=True)

# ============== COUNTRY POLICY CONTEXT ==============
policy = POLICY.get(iso, {})
if policy.get("policies"):
    eyebrow(t("profile.policy_eyebrow"))
    st.markdown(f"<h3>{t('profile.policy_h3', country=country_name(iso))}</h3>", unsafe_allow_html=True)
    st.markdown(
        f'<p style="font-size:14px;line-height:1.65;color:var(--ink-soft);margin-bottom:6px;">'
        f'{tk(f"policy.{iso}.summary", policy.get("summary", ""))}</p>'
        f'<p style="font-size:11px;line-height:1.5;color:var(--ink-soft);opacity:0.75;margin-bottom:16px;">'
        f'{t("profile.policy_note", country=country_name(iso), loc=loc_display)}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "".join(
            f'<p style="font-size:14px;line-height:1.65;color:var(--ink-soft);margin-bottom:12px;">'
            f'<strong style="color:var(--ink);">{tk(f"policy.{iso}.{i}.name", n)}.</strong> '
            f'{tk(f"policy.{iso}.{i}.desc", d)}</p>'
            for i, (n, d) in enumerate(policy["policies"])
        ),
        unsafe_allow_html=True,
    )


render_footer()
