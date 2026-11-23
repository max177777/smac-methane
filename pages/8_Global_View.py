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

# ============== NOTHING PICKED: global leaderboard as a starting point ==============
if gid is None:
    rank = gd.year_ranking(year)
    n_mo = len(gd.monthly().query("year == @year")["month"].unique())
    _part = t("global.first_months", n=n_mo) if 0 < n_mo < 12 else ""
    eyebrow(t("global.lead_eyebrow"))
    _view = st.radio(t("global.lead_view"), ["sub", "country"], horizontal=True,
                     format_func=lambda v: t("global.lead_view_sub") if v == "sub" else t("global.lead_view_country"),
                     key="gv_lead_view", label_visibility="collapsed")
    if _view == "country":
        ct = gd.country_year_totals(year).head(15)
        ct["value"] = ct["national"].fillna(ct["subnational_sum"])
        d = ct.sort_values("value")
        st.markdown(f"<h3>{t('global.lead_country_h3', y=year)}{_part}</h3>", unsafe_allow_html=True)
        _labels = [country_name(r.iso3, r.country_name) for r in d.itertuples()]
        _x = d["value"]
        _custom = d["n_admins"]
        _hover = "<b>%{y}</b><br>%{x:,.0f} t CH₄<br>" + t("global.hover_n_admins") + "<extra></extra>"
    else:
        top = rank.nsmallest(15, "rank_world").merge(adm[["gadm_id", "location", "country_name"]],
                                                     on="gadm_id")  # rank already carries iso3
        st.markdown(f"<h3>{t('global.lead_h3', y=year)}{_part}</h3>", unsafe_allow_html=True)
        d = top.sort_values("ch4_tonnes")
        _labels = [f"{r.location}, {country_name(r.iso3, r.country_name)}" for r in d.itertuples()]
        _x = d["ch4_tonnes"]
        _custom = None
        _hover = "<b>%{y}</b><br>%{x:,.0f} t CH₄<extra></extra>"
    fig = go.Figure(go.Bar(
        x=_x,
        y=_labels,
        customdata=_custom,
        orientation="h",
        marker_color="#0e9d6c",
        hovertemplate=_hover,
    ))
    fig.update_layout(height=460, margin=dict(l=0, r=10, t=6, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(title="CH₄ (t)", tickformat=",.0f", gridcolor=LINE_SOFT),
                      font=dict(family="Inter, sans-serif", size=12))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    if _view == "country":
        _note = ("global.country_basis_national" if gd.national_monthly().shape[0]
                 else "global.country_basis_sum")
        st.markdown(f'<div class="smac-meta" style="font-size:10px;margin-bottom:6px;">{t(_note)}</div>',
                    unsafe_allow_html=True)
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
