"""
Global View of Methane.
For jurisdictions OUTSIDE the coalition (it works for members too): type any
state, province or region Climate TRACE covers and get the basics — total and
trend, sector mix, and the top 20 emitting facilities. Deliberately lighter
than the SMAC Members page, which keeps the document library, action plans and
sub-sector drill-down. Data: data/global/, built by scripts/fetch_climatetrace_all.py.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.theme import inject_theme, eyebrow, render_footer
from utils.data_loader import CURRENT_YEAR, CT_SNAPSHOT_DATE, CT_API_VERSION, fmt_mt, fmt_int, display_name
from utils.policy_content import GWP100, GWP20
from utils.charts import time_series_plotly, sector_trend_plotly, SECTOR_COLORS, LINE_SOFT
from utils import global_data as gd
from utils.i18n import t, sector_name, country_name

inject_theme()

eyebrow(t("global.eyebrow"))
st.markdown(f"<h1 style='margin-bottom:8px;'>{t('global.title')}</h1>", unsafe_allow_html=True)

if not gd.has_global_data():
    st.info(t("global.no_data"), icon="🌍")
    render_footer()
    st.stop()

adm = gd.admins()
st.markdown(
    f'<p style="font-family:Inter,sans-serif;font-size:16px;line-height:1.6;color:var(--ink-soft);'
    f'max-width:720px;margin-bottom:6px;">'
    f"{t('global.intro', n=f'{len(adm):,}', c=adm['iso3'].nunique())}</p>"
    f'<div class="smac-meta" style="font-size:10px;margin-bottom:18px;opacity:0.85;">'
    f"{t('global.snapshot', date=CT_SNAPSHOT_DATE, api=CT_API_VERSION)}</div>",
    unsafe_allow_html=True,
)

# ============== PICKERS ==============
if "gv_pending" in st.session_state:          # set by clicking a bar on the overview
    st.session_state["gv_admin"] = st.session_state.pop("gv_pending")
years = [y for y in gd.data_years() if y <= CURRENT_YEAR + 1]
pc1, pc2 = st.columns([3, 1], gap="medium")
with pc1:
    keys = adm["gadm_id"].tolist()
    # SMAC countries show their name in the active language; the rest keep the
    # dataset's own name. The label still carries the plain-ASCII alias for search.
    labels = {r.gadm_id: r.label.replace(f"  ·  {r.country_name}",
                                         f"  ·  {country_name(r.iso3, r.country_name)}", 1)
              for r in adm.itertuples()}
    gid = st.selectbox(
        t("global.picker"), options=keys, index=None,
        format_func=lambda k: labels[k],
        placeholder=t("global.placeholder"),
        filter_mode="contains", key="gv_admin",
    )
with pc2:
    year = st.selectbox(t("common.year"), options=list(reversed(years)),
                        index=list(reversed(years)).index(CURRENT_YEAR) if CURRENT_YEAR in years else 0,
                        key="gv_year")

# ============== NOTHING PICKED: global overview ==============
# Nov-2026: KPIs, a world map, sector-aware leaderboards, the global sector mix,
# concentration and the biggest movers — all from data/global/. One sector
# picker drives the map, leaderboard, concentration and movers.
if gid is None:
    import numpy as np
    from utils.charts import COPPER

    _ALL = "__all__"
    n_mo = len(gd.months_in_year(year))
    _part = t("global.first_months", n=n_mo) if 0 < n_mo < 12 else ""

    eyebrow(t("global.overview_eyebrow"))
    sc1, sc2 = st.columns([1.2, 2], vertical_alignment="bottom")
    with sc1:
        _sec_opt = st.selectbox(
            t("global.sector_filter"), [_ALL] + gd.global_sectors(), key="gv_sector",
            format_func=lambda s: t("profile.ts_all_sectors") if s == _ALL else sector_name(s))
    sec = None if _sec_opt == _ALL else _sec_opt
    sec_label = t("profile.ts_all_sectors") if sec is None else sector_name(sec)
    accent = "#0e9d6c" if sec is None else SECTOR_COLORS.get(sec, "#0e9d6c")
    with sc2:
        if _part:
            st.markdown(f'<div class="smac-meta" style="font-size:10px;padding-bottom:12px;">'
                        f'{t("common.partial_year_warn", y=year, n=n_mo)}</div>', unsafe_allow_html=True)

    av = gd.admin_values(year, sec)
    cv = gd.country_values(year, sec)
    all_total = gd.admin_values(year)["ch4_tonnes"].sum()
    sel_total = av["ch4_tonnes"].sum()

    # ---------- KPI strip (HTML cards: long labels/values wrap instead of truncating)
    def _kpi(col, label, value, sub=None, sub_color="var(--ink-soft)"):
        col.markdown(
            '<div style="background:var(--paper-2);border:1px solid var(--line);border-radius:14px;'
            'padding:16px 18px;height:100%;min-height:118px;">'
            f'<div style="font-family:Inter,sans-serif;font-size:11px;letter-spacing:0.08em;text-transform:uppercase;'
            f'color:var(--ink-soft);line-height:1.35;">{label}</div>'
            f'<div style="font-family:Quicksand,Inter,sans-serif;font-weight:700;font-size:26px;line-height:1.15;'
            f'color:var(--ink);margin-top:6px;">{value}</div>'
            + (f'<div style="font-size:12px;font-weight:600;color:{sub_color};margin-top:6px;">{sub}</div>' if sub else "")
            + "</div>", unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    _delta, _dcol = None, "var(--ink-soft)"
    _pct = None
    if sec is None:
        lfl = gd.world_like_for_like(year)
        _pct = lfl["pct"]
        if _pct is not None:
            _delta = (t("profile.delta_partial", pct=f"{_pct:+.1f}", n=n_mo, py=year - 1)
                      if lfl["is_partial"] else t("profile.delta_yoy", pct=f"{_pct:+.1f}"))
    elif n_mo == 12 and year - 1 in gd.data_years():
        _prev = gd.admin_values(year - 1, sec)["ch4_tonnes"].sum()
        if _prev:
            _pct = (sel_total - _prev) / _prev * 100
            _delta = t("profile.delta_yoy", pct=f"{_pct:+.1f}")
    if _pct is not None:   # more methane = red, less = green
        _dcol = "#e2574c" if _pct > 0 else "#0e9d6c"
        _delta = ("↑ " if _pct > 0 else "↓ ") + _delta
    _kpi(k1, t("global.kpi_world_total", y=year), f"{fmt_mt(sel_total)} Mt", _delta, _dcol)
    _kpi(k2, t("global.kpi_coverage"), f"{len(av):,}", t("global.kpi_coverage_delta", c=av["iso3"].nunique()))
    _top100 = av["ch4_tonnes"].head(100).sum() / sel_total * 100 if sel_total else 0
    _kpi(k3, t("global.kpi_top100"), f"{_top100:.0f}%", t("global.kpi_top100_delta", n=f"{len(av):,}"))
    if sec is None:
        _mix = gd.global_sector_trend().query("year == @year").sort_values("ch4_tonnes", ascending=False)
        _top = _mix.iloc[0]
        _kpi(k4, t("global.kpi_top_sector"),
             f'<span style="font-size:19px;color:{SECTOR_COLORS.get(_top["sector"], "#12161a")};">'
             f'{sector_name(_top["sector"])}</span>',
             t("global.kpi_top_sector_delta", pct=f"{_top['ch4_tonnes'] / all_total * 100:.0f}"))
    else:
        _kpi(k4, t("global.kpi_sector_share"), f"{sel_total / all_total * 100:.1f}%" if all_total else "—",
             t("global.kpi_sector_share_delta", y=year))

    # ---------- world map (countries = sum of their regions)
    def _ramp(hex_color: str, all_sectors: bool) -> list:
        """Light-to-dark colour scale in one hue (mint/forest for all sectors)."""
        if all_sectors:
            return [[0, "#eef6f2"], [0.35, "#9fdcc0"], [0.7, "#0e9d6c"], [1, "#0b3d2a"]]
        h = hex_color.lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        mix = lambda w, k: "#%02x%02x%02x" % tuple(int(c * w + k * (1 - w)) for c in (r, g, b))
        return [[0, mix(0.10, 255)], [0.4, mix(0.55, 255)], [0.75, mix(1.0, 0)], [1, mix(0.6, 0)]]

    st.markdown("<br>", unsafe_allow_html=True)
    eyebrow(t("global.map_eyebrow"))
    st.markdown(f"<h3>{t('global.map_h3', sector=sec_label, y=year)}{_part}</h3>", unsafe_allow_html=True)
    _cv = cv[cv["ch4_tonnes"] > 0]
    _z = np.log10(_cv["ch4_tonnes"].clip(lower=1))
    _lo, _hi = max(0, int(np.floor(_z.quantile(0.02)))), int(np.ceil(_z.max()))
    _ticks = list(range(_lo, _hi + 1))
    _ticklab = [("1" if v == 0 else f"{10 ** v / 1e6:g} Mt" if v >= 6 else f"{10 ** v / 1e3:g}k t" if v >= 3
                 else f"{10 ** v:g} t") for v in _ticks]
    fig = go.Figure(go.Choropleth(
        locations=_cv["iso3"], z=_z, locationmode="ISO-3", zmin=_lo, zmax=_hi,
        colorscale=_ramp(accent, sec is None),
        marker_line_color="#ffffff", marker_line_width=0.4,
        customdata=np.stack([[country_name(r.iso3, r.country_name) for r in _cv.itertuples()],
                             (_cv["ch4_tonnes"] / 1e6).round(3), _cv["n_admins"]], axis=-1),
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} Mt CH₄<br>"
                      + t("global.hover_n_admins").replace("%{customdata}", "%{customdata[2]}") + "<extra></extra>",
        colorbar=dict(tickvals=_ticks, ticktext=_ticklab, thickness=10, len=0.7, outlinewidth=0,
                      tickfont=dict(size=10, color="#566058"), x=1.0),
    ))
    fig.update_geos(projection_type="natural earth", showframe=False, showcoastlines=False,
                    showland=True, landcolor="#f1f4f2", showcountries=True, countrycolor="#ffffff",
                    showocean=False, showlakes=False, bgcolor="rgba(0,0,0,0)", lataxis_range=[-58, 85])
    fig.update_layout(height=470, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, sans-serif", size=12), dragmode=False)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})
    st.markdown(f'<div class="smac-meta" style="font-size:10px;">{t("global.map_note")}</div>',
                unsafe_allow_html=True)

    # ---------- leaderboard (left) + global sector mix (right)
    st.markdown("<br>", unsafe_allow_html=True)
    lc, rc = st.columns([1.15, 1], gap="large")
    with lc:
        eyebrow(t("global.lead_eyebrow"))
        _view = st.radio(t("global.lead_view"), ["sub", "country"], horizontal=True,
                         format_func=lambda v: t("global.lead_view_sub") if v == "sub" else t("global.lead_view_country"),
                         key="gv_lead_view", label_visibility="collapsed")
        if _view == "country":
            d = cv.head(15).iloc[::-1]
            if sec is None and gd.national_monthly().shape[0]:   # official national totals, when fetched
                ct = gd.country_year_totals(year)
                ct["value"] = ct["national"].fillna(ct["subnational_sum"])
                d = ct.head(15).rename(columns={"value": "ch4_tonnes"}).iloc[::-1]
            st.markdown(f"<h3>{t('global.lead_country_sector_h3', sector=sec_label, y=year)}{_part}</h3>",
                        unsafe_allow_html=True)
            _labels = [country_name(r.iso3, r.country_name) for r in d.itertuples()]
            _custom = d["n_admins"]
            _hover = "<b>%{y}</b><br>%{x:,.0f} t CH₄<br>" + t("global.hover_n_admins") + "<extra></extra>"
        else:
            d = av.head(15).iloc[::-1]
            st.markdown(f"<h3>{t('global.lead_sector_h3', sector=sec_label, y=year)}{_part}</h3>",
                        unsafe_allow_html=True)
            _labels = [f"{r.location}, {country_name(r.iso3, r.country_name)}" for r in d.itertuples()]
            _custom = d["gadm_id"]
            _hover = "<b>%{y}</b><br>%{x:,.0f} t CH₄<extra></extra>"
        fig = go.Figure(go.Bar(x=d["ch4_tonnes"], y=_labels, customdata=_custom, orientation="h",
                               marker_color=accent, hovertemplate=_hover))
        fig.update_layout(height=470, margin=dict(l=0, r=10, t=6, b=10),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          xaxis=dict(title="CH₄ (t)", tickformat="~s", gridcolor=LINE_SOFT, tickangle=0, nticks=6),
                          font=dict(family="Inter, sans-serif", size=12), dragmode=False)
        _ck = f"gv_lead_{st.session_state.get('gv_click_n', 0)}"
        if _view == "sub":   # click a bar -> open that region's profile
            ev = st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False},
                                 on_select="rerun", selection_mode="points", key=_ck)
            _pts = (ev or {}).get("selection", {}).get("points", []) if ev else []
            if _pts and _pts[0].get("customdata"):
                _cd = _pts[0]["customdata"]
                st.session_state["gv_pending"] = _cd[0] if isinstance(_cd, list) else _cd
                st.session_state["gv_click_n"] = st.session_state.get("gv_click_n", 0) + 1
                st.rerun()
            st.markdown(f'<div class="smac-meta" style="font-size:10px;">{t("global.click_hint")}</div>',
                        unsafe_allow_html=True)
        else:
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            _note = ("global.country_basis_national" if sec is None and gd.national_monthly().shape[0]
                     else "global.country_basis_sum")
            st.markdown(f'<div class="smac-meta" style="font-size:10px;">{t(_note)}</div>', unsafe_allow_html=True)
    with rc:
        eyebrow(t("global.mix_eyebrow"))
        _gt = gd.global_sector_trend()
        _yrs = sorted(_gt["year"].unique())
        st.markdown(f"<h3>{t('global.mix_h3', y0=_yrs[0], y1=_yrs[-1])}</h3>", unsafe_allow_html=True)
        fig = sector_trend_plotly(_gt, height=470)
        fig.update_yaxes(tickformat="~s")
        fig.update_layout(margin=dict(l=10, r=10, t=96, b=10), paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)",
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, bgcolor="rgba(0,0,0,0)"))
        if sec is not None:   # fade every sector except the one picked
            for tr in fig.data:
                tr.opacity = 1.0 if tr.name == sector_name(sec) or tr.name == sec else 0.18
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        if _yrs[-1] in set(gd.data_years()) and len(gd.months_in_year(_yrs[-1])) < 12:
            st.markdown(f'<div class="smac-meta" style="font-size:10px;">'
                        f'{t("common.partial_year_warn", y=_yrs[-1], n=len(gd.months_in_year(_yrs[-1])))}</div>',
                        unsafe_allow_html=True)

    # ---------- concentration (left) + biggest movers (right)
    st.markdown("<br>", unsafe_allow_html=True)
    cc, mc = st.columns([1, 1.15], gap="large")
    with cc:
        eyebrow(t("global.conc_eyebrow"))
        st.markdown(f"<h3>{t('global.conc_h3')}</h3>", unsafe_allow_html=True)
        _cum = (av["ch4_tonnes"].cumsum() / sel_total * 100).values if sel_total else np.array([])
        _n = np.arange(1, len(_cum) + 1)
        fig = go.Figure(go.Scatter(x=_n, y=_cum, mode="lines", line=dict(color=accent, width=2.5),
                                   fill="tozeroy", fillcolor="rgba(14,157,108,0.10)" if sec is None else None,
                                   hovertemplate=t("global.conc_hover") + "<extra></extra>"))
        _marks = [k for k in (10, 100, 1000) if k <= len(_cum)]
        for k in _marks:
            fig.add_trace(go.Scatter(x=[k], y=[_cum[k - 1]], mode="markers+text", marker=dict(size=9, color=accent),
                                     text=[f"  {_cum[k - 1]:.0f}%"], textposition="middle right",
                                     textfont=dict(size=12, color="#12161a"), hoverinfo="skip", showlegend=False))
        fig.update_layout(height=360, margin=dict(l=0, r=10, t=6, b=10), showlegend=False,
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          xaxis=dict(type="log", title=t("global.conc_x"), gridcolor=LINE_SOFT,
                                     range=[0, np.log10(max(len(_cum), 10)) + 0.45]),
                          yaxis=dict(title=t("global.conc_y"), range=[0, 102], gridcolor=LINE_SOFT, ticksuffix="%"),
                          font=dict(family="Inter, sans-serif", size=12), dragmode=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        if _marks:
            st.markdown(f'<div class="smac-meta" style="font-size:10px;">'
                        f'{t("global.conc_note", a=_marks[0], pa=f"{_cum[_marks[0] - 1]:.0f}", n=f"{len(av):,}")}</div>',
                        unsafe_allow_html=True)
    with mc:
        eyebrow(t("global.movers_eyebrow"))
        st.markdown(f"<h3>{t('global.movers_h3', py=year - 1, y=year)}</h3>", unsafe_allow_html=True)
        mv = gd.movers(year, sec) if (year - 1) in set(gd.data_years()) else None
        if mv is None or mv.empty:
            st.info(t("global.movers_full_only") if sec is not None else t("global.no_sector"))
        else:
            fig = go.Figure(go.Bar(
                x=mv["change"], y=[f"{r.location}, {country_name(r.iso3, r.country_name)}" for r in mv.itertuples()],
                customdata=mv["gadm_id"], orientation="h",
                marker_color=["#e2574c" if c > 0 else "#0e9d6c" for c in mv["change"]],
                hovertemplate="<b>%{y}</b><br>%{x:+,.0f} t CH₄<extra></extra>"))
            fig.update_layout(height=360 if len(mv) <= 12 else 420, margin=dict(l=0, r=10, t=6, b=10),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              xaxis=dict(title=t("global.movers_x"), tickformat="~s", gridcolor=LINE_SOFT,
                                         tickangle=0, nticks=6, zeroline=True, zerolinecolor="#8a948e"),
                              font=dict(family="Inter, sans-serif", size=12), dragmode=False)
            _mk = f"gv_movers_{st.session_state.get('gv_click_n', 0)}"
            ev = st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False},
                                 on_select="rerun", selection_mode="points", key=_mk)
            _pts = (ev or {}).get("selection", {}).get("points", []) if ev else []
            if _pts and _pts[0].get("customdata"):
                _cd = _pts[0]["customdata"]
                st.session_state["gv_pending"] = _cd[0] if isinstance(_cd, list) else _cd
                st.session_state["gv_click_n"] = st.session_state.get("gv_click_n", 0) + 1
                st.rerun()
            st.markdown(f'<div class="smac-meta" style="font-size:10px;">'
                        f'{t("global.movers_note" if sec is None else "global.movers_note_sector")}</div>',
                        unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div class="smac-meta">{t("global.pick_hint")}</div>', unsafe_allow_html=True)
    render_footer()
    st.stop()

# ============== HEADER ==============
row = adm[adm["gadm_id"] == gid].iloc[0]
loc, country = row["location"], country_name(row["iso3"], row["country_name"])
if isinstance(row["smac_key"], str):  # SMAC members use their roster display name (e.g. "Catalonia")
    loc = display_name(row["smac_key"].split("||", 1)[1])
st.markdown(
    f'<div class="smac-meta" style="margin-top:10px;">{country} &nbsp;·&nbsp; {row["name"]}</div>'
    f"<h1 style='font-size:3rem;margin-top:6px;margin-bottom:6px;'>{loc}</h1>",
    unsafe_allow_html=True,
)

if isinstance(row["smac_key"], str):
    s_iso, s_loc = row["smac_key"].split("||", 1)
    st.markdown(f'<span class="smac-pill">{t("common.smac_member_pill")}</span>', unsafe_allow_html=True)
    if st.button(t("global.open_smac", loc=loc), key="gv_to_smac"):
        st.session_state.smac_jurisdiction = (s_iso, s_loc)
        st.switch_page("pages/2_Country_Profile.py")
else:
    st.markdown(
        f'<div class="smac-meta" style="font-size:11px;">{t("global.not_member")}</div>',
        unsafe_allow_html=True,
    )

lfl = gd.admin_like_for_like(gid, year)
if lfl["n_months"] == 0:
    st.info(t("compare.no_data", y=year, label=loc))
    render_footer()
    st.stop()

rank = gd.year_ranking(year)
rr = rank[rank["gadm_id"] == gid]
st.markdown("<br>", unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
_yoy_nan = lfl["yoy_pct"] != lfl["yoy_pct"]
with k1:
    st.metric(
        (t("profile.kpi_partial", y=year, n=lfl["n_months"]) if lfl["is_partial"]
         else t("profile.kpi_total", y=year)),
        f"{fmt_mt(lfl['total'])} Mt",
        "—" if _yoy_nan else (t("profile.delta_partial", pct=f"{lfl['yoy_pct']:+.1f}",
                                n=lfl["n_months"], py=year - 1)
                              if lfl["is_partial"] else t("profile.delta_yoy", pct=f"{lfl['yoy_pct']:+.1f}")),
        delta_color="off" if _yoy_nan else ("inverse" if lfl["yoy_pct"] > 0 else "normal"),
    )
with k2:
    st.metric(t("common.gwp100_label", y=year), f"{fmt_mt(lfl['total'] * GWP100)} Mt",
              t("common.ipcc_factor", f=GWP100), delta_color="off")
with k3:
    st.metric(t("common.gwp20_label", y=year), f"{fmt_mt(lfl['total'] * GWP20)} Mt",
              t("common.ipcc_factor", f=GWP20), delta_color="off")
with k4:
    if len(rr):
        r0 = rr.iloc[0]
        st.metric(t("global.world_rank"),
                  t("profile.rank_of", pos=f"{int(r0['rank_world']):,}", n=f"{len(rank):,}"),
                  t("global.country_rank", pos=int(r0["rank_country"]), n=int(r0["n_country"]),
                    country=country),
                  delta_color="off", help=t("global.rank_help"))
if lfl["is_partial"]:
    st.markdown(
        f'<div class="smac-meta" style="font-size:10px;">'
        f'{t("common.partial_year_warn", y=year, n=lfl["n_months"])}</div>',
        unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============== COUNTRY CONTEXT: this region vs the country total ==============
# Nov-2026 feedback — e.g. Germany's 16 Länder vs Germany's total.
_ct = gd.country_year_totals(year)
_ct = _ct[_ct["iso3"] == row["iso3"]]
if len(_ct):
    c0 = _ct.iloc[0]
    _ca = gd.country_admins(row["iso3"], year)
    _share = float(_ca.loc[_ca["gadm_id"] == gid, "share_pct"].sum())
    _has_nat = c0["national"] == c0["national"]   # not NaN
    eyebrow(t("global.country_eyebrow"))
    st.markdown(f"<h3>{t('global.country_h3', loc=loc, country=country, y=year)}</h3>",
                unsafe_allow_html=True)
    q1, q2, q3 = st.columns(3)
    with q1:
        st.metric(t("global.kpi_country_sum", n=int(c0["n_admins"])), f"{fmt_mt(c0['subnational_sum'])} Mt",
                  t("global.kpi_country_rank", pos=int(c0["rank"]), n=len(gd.country_year_totals(year))),
                  delta_color="off", help=t("global.help_country_sum"))
    with q2:
        st.metric(t("global.kpi_share", loc=loc), f"{_share:.1f}%",
                  t("global.kpi_share_delta", pos=int(rr.iloc[0]["rank_country"]) if len(rr) else 0,
                    n=int(c0["n_admins"])),
                  delta_color="off")
    with q3:
        if _has_nat:
            _un = c0["unattributed"]
            st.metric(t("global.kpi_national"), f"{fmt_mt(c0['national'])} Mt",
                      t("global.kpi_unattributed", v=fmt_mt(_un),
                        pct=f"{_un / c0['national'] * 100:.1f}" if c0["national"] else "0"),
                      delta_color="off", help=t("global.help_national"))
        else:
            st.metric(t("global.kpi_national"), "—", t("global.national_pending"), delta_color="off",
                      help=t("global.help_national"))

    # Bar: every admin in the country (top 14 + the rest), this one highlighted.
    _top = _ca if len(_ca) <= 16 else _ca.head(14)
    if gid not in set(_top["gadm_id"]):
        _top = pd.concat([_top.head(13), _ca[_ca["gadm_id"] == gid]])
    _rest = _ca[~_ca["gadm_id"].isin(_top["gadm_id"])]
    _bars = [(r.location, r.ch4_tonnes, r.gadm_id == gid) for r in _top.itertuples()]
    if len(_rest):
        _bars.append((t("global.other_admins", n=len(_rest)), _rest["ch4_tonnes"].sum(), False))
    if _has_nat and c0["unattributed"] > 0:
        _bars.append((t("global.unattributed_bar"), c0["unattributed"], None))
    _bars = _bars[::-1]
    _colors = ["#0e9d6c" if h else ("#d7ddd9" if h is None else "#a9c9bb") for _, _, h in _bars]
    fig = go.Figure(go.Bar(
        x=[v for _, v, _ in _bars], y=[n for n, _, _ in _bars], orientation="h",
        marker=dict(color=_colors, line=dict(color=["#0e9d6c" if h else "rgba(0,0,0,0)" for _, _, h in _bars],
                                             width=1)),
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} t CH₄<extra></extra>",
    ))
    fig.update_layout(height=max(220, 26 * len(_bars) + 40), margin=dict(l=0, r=10, t=6, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(title="CH₄ (t)", tickformat=",.0f", gridcolor=LINE_SOFT),
                      font=dict(family="Inter, sans-serif", size=12))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown(f'<div class="smac-meta" style="font-size:10px;">'
                f'{t("global.country_basis_national" if _has_nat else "global.country_basis_sum")}</div>',
                unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ============== TREND + SECTOR MIX ==============
ca, cb = st.columns([1.3, 1], gap="large")
with ca:
    eyebrow(t("common.monthly_series"))
    st.markdown(f"<h3>{t('global.per_month')}</h3>", unsafe_allow_html=True)
    st.plotly_chart(time_series_plotly(gd.admin_monthly(gid), height=300),
                    use_container_width=True, config={"displayModeBar": False})
with cb:
    eyebrow(t("common.sector_breakdown"))
    st.markdown(f"<h3>{year}</h3>", unsafe_allow_html=True)
    sec = gd.admin_sectors(gid, year)
    if sec.empty:
        st.info(t("global.no_sector"))
    else:
        fig = go.Figure(go.Pie(
            labels=[sector_name(x) for x in sec["sector"]], values=sec["ch4_tonnes"], hole=0.5,
            marker=dict(colors=[SECTOR_COLORS.get(s, "#b9c4bd") for s in sec["sector"]]),
            textinfo="percent", textfont=dict(family="Quicksand, sans-serif", size=11),
        ))
        fig.update_layout(height=300, showlegend=True, margin=dict(l=0, r=0, t=10, b=10),
                          legend=dict(font=dict(size=10, family="Quicksand, sans-serif")),
                          paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

eyebrow(t("global.mix_over_time"))
st.plotly_chart(sector_trend_plotly(gd.admin_sector_trend(gid), height=300),
                use_container_width=True, config={"displayModeBar": False})

# ============== TOP 20 FACILITIES ==============
fac, fac_year = gd.admin_facilities(gid, year)
eyebrow(t("common.top_sources"))
if fac.empty:
    st.info(t("global.no_fac", loc=loc))
else:
    note = "" if fac_year == year else t("global.fac_year_note", y=fac_year)
    st.markdown(f"<h3>{t('global.fac_h3', n=len(fac), y=fac_year)}{note}</h3>", unsafe_allow_html=True)
    st.markdown(f'<div class="smac-meta" style="margin-bottom:12px;">{t("global.fac_note")}</div>',
                unsafe_allow_html=True)
    _cols = [t("common.facility"), t("common.type"), t("common.sector"), t("common.subsector"),
             t("common.ch4_t_col", y=fac_year)]
    show = fac.rename(columns=dict(zip(
        ["source_name", "asset_type", "sector", "sub_sector", "ch4_tonnes"], _cols)))[_cols]
    st.dataframe(show, hide_index=True, use_container_width=True, height=420,
                 column_config={_cols[-1]: st.column_config.NumberColumn(format="localized")})
    pts = fac.dropna(subset=["lat", "lon"])
    if not pts.empty:
        st.map(pts.rename(columns={"lat": "latitude", "lon": "longitude"})[["latitude", "longitude"]],
               size=400)

# ============== CTA ==============
if not isinstance(row["smac_key"], str):
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="smac-card" style="padding:20px 24px;max-width:760px;border-left:4px solid var(--mint);">'
        f'<div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:16px;margin-bottom:6px;">'
        f'{t("global.cta_title", loc=loc)}</div>'
        f'<div style="font-size:13.5px;line-height:1.6;color:var(--ink-soft);">{t("global.cta_body")}</div></div>',
        unsafe_allow_html=True,
    )
    if st.button(t("global.cta_button"), key="gv_contact"):
        st.switch_page("pages/6_Contact.py")

render_footer()
