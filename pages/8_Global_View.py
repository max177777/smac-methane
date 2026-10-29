"""
Global View of Methane.
For jurisdictions OUTSIDE the coalition (it works for members too): type any
state, province or region Climate TRACE covers and get the basics — total and
trend, sector mix, and the top 20 emitting facilities. Deliberately lighter
than the SMAC Members page, which keeps the document library, action plans and
sub-sector drill-down. Data: data/global/, built by scripts/fetch_climatetrace_all.py.
"""

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
    top = rank.nsmallest(15, "rank_world").merge(adm[["gadm_id", "location", "country_name"]],
                                                 on="gadm_id")  # rank already carries iso3
    eyebrow(t("global.lead_eyebrow"))
    _part = t("global.first_months", n=n_mo) if 0 < n_mo < 12 else ""
    st.markdown(f"<h3>{t('global.lead_h3', y=year)}{_part}</h3>", unsafe_allow_html=True)
    d = top.sort_values("ch4_tonnes")
    fig = go.Figure(go.Bar(
        x=d["ch4_tonnes"],
        y=[f"{r.location}, {country_name(r.iso3, r.country_name)}" for r in d.itertuples()],
        orientation="h",
        marker_color="#0e9d6c",
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} t CH₄<extra></extra>",
    ))
    fig.update_layout(height=460, margin=dict(l=0, r=10, t=6, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(title="CH₄ (t)", tickformat=",.0f", gridcolor=LINE_SOFT),
                      font=dict(family="Inter, sans-serif", size=12))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
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
