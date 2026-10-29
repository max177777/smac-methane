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
from utils.data_loader import CURRENT_YEAR, CT_SNAPSHOT_DATE, CT_API_VERSION, fmt_mt, fmt_int
from utils.policy_content import GWP100, GWP20
from utils.charts import time_series_plotly, sector_trend_plotly, SECTOR_COLORS, LINE_SOFT
from utils import global_data as gd

inject_theme()

eyebrow("Global View of Methane")
st.markdown("<h1 style='margin-bottom:8px;'>Methane in <em>any</em> state or province.</h1>",
            unsafe_allow_html=True)

if not gd.has_global_data():
    st.info(
        "The global dataset hasn't been loaded yet. It is built offline with "
        "`python scripts/fetch_climatetrace_all.py` and committed under `data/global/`.",
        icon="🌍",
    )
    render_footer()
    st.stop()

adm = gd.admins()
st.markdown(
    f'<p style="font-family:Inter,sans-serif;font-size:16px;line-height:1.6;color:var(--ink-soft);'
    f'max-width:720px;margin-bottom:6px;">'
    f"Climate TRACE methane estimates for <strong>{len(adm):,} subnational jurisdictions</strong> "
    f"across <strong>{adm['iso3'].nunique()} countries</strong> — including places that aren't "
    f"SMAC members yet. Type a name to see its total, trend, sector mix and largest "
    f"emitting facilities.</p>"
    f'<div class="smac-meta" style="font-size:10px;margin-bottom:18px;opacity:0.85;">'
    f"Climate TRACE snapshot: pulled {CT_SNAPSHOT_DATE} via API {CT_API_VERSION} · modeled "
    f"estimates, not measurements — see Data &amp; Methods</div>",
    unsafe_allow_html=True,
)

# ============== PICKERS ==============
years = [y for y in gd.data_years() if y <= CURRENT_YEAR + 1]
pc1, pc2 = st.columns([3, 1], gap="medium")
with pc1:
    keys = adm["gadm_id"].tolist()
    labels = dict(zip(adm["gadm_id"], adm["label"]))
    gid = st.selectbox(
        "Jurisdiction", options=keys, index=None,
        format_func=lambda k: labels[k],
        placeholder="Type a state, province or region…  e.g. Texas, Punjab, Bavaria",
        filter_mode="contains", key="gv_admin",
    )
with pc2:
    year = st.selectbox("Year", options=list(reversed(years)),
                        index=list(reversed(years)).index(CURRENT_YEAR) if CURRENT_YEAR in years else 0,
                        key="gv_year")

# ============== NOTHING PICKED: global leaderboard as a starting point ==============
if gid is None:
    rank = gd.year_ranking(year)
    n_mo = len(gd.monthly().query("year == @year")["month"].unique())
    top = rank.nsmallest(15, "rank_world").merge(adm[["gadm_id", "location", "country_name"]],
                                                 on="gadm_id")
    eyebrow("Largest emitters worldwide")
    st.markdown(f"<h3>Top 15 subnational methane emitters · {year}"
                f"{f' (first {n_mo} months)' if 0 < n_mo < 12 else ''}</h3>",
                unsafe_allow_html=True)
    d = top.sort_values("ch4_tonnes")
    fig = go.Figure(go.Bar(
        x=d["ch4_tonnes"], y=d["location"] + ", " + d["country_name"], orientation="h",
        marker_color="#0e9d6c",
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} t CH₄<extra></extra>",
    ))
    fig.update_layout(height=460, margin=dict(l=0, r=10, t=6, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(title="CH₄ (t)", tickformat=",.0f", gridcolor=LINE_SOFT),
                      font=dict(family="Inter, sans-serif", size=12))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('<div class="smac-meta">pick any jurisdiction above to see its own profile</div>',
                unsafe_allow_html=True)
    render_footer()
    st.stop()

# ============== HEADER ==============
row = adm[adm["gadm_id"] == gid].iloc[0]
loc, country = row["location"], row["country_name"]
st.markdown(
    f'<div class="smac-meta" style="margin-top:10px;">{country} &nbsp;·&nbsp; {row["name"]}</div>'
    f"<h1 style='font-size:3rem;margin-top:6px;margin-bottom:6px;'>{loc}</h1>",
    unsafe_allow_html=True,
)

if isinstance(row["smac_key"], str):
    s_iso, s_loc = row["smac_key"].split("||", 1)
    st.markdown('<span class="smac-pill">● SMAC member</span>', unsafe_allow_html=True)
    if st.button(f"Open the full SMAC profile for {loc} →", key="gv_to_smac"):
        st.session_state.smac_jurisdiction = (s_iso, s_loc)
        st.switch_page("pages/2_Country_Profile.py")
else:
    st.markdown(
        '<div class="smac-meta" style="font-size:11px;">not a SMAC member · '
        'joining is free — see <strong>Contact</strong></div>',
        unsafe_allow_html=True,
    )

lfl = gd.admin_like_for_like(gid, year)
if lfl["n_months"] == 0:
    st.info(f"No {year} data for {loc}.")
    render_footer()
    st.stop()

rank = gd.year_ranking(year)
rr = rank[rank["gadm_id"] == gid]
st.markdown("<br>", unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
_yoy_nan = lfl["yoy_pct"] != lfl["yoy_pct"]
with k1:
    st.metric(
        f"{year} CH₄" + (f" · first {lfl['n_months']} months" if lfl["is_partial"] else ""),
        f"{fmt_mt(lfl['total'])} Mt",
        "—" if _yoy_nan else (f"{lfl['yoy_pct']:+.1f}% vs same months {year - 1}"
                              if lfl["is_partial"] else f"{lfl['yoy_pct']:+.1f}% YoY"),
        delta_color="off" if _yoy_nan else ("inverse" if lfl["yoy_pct"] > 0 else "normal"),
    )
with k2:
    st.metric(f"CO₂e · GWP100 · {year}", f"{fmt_mt(lfl['total'] * GWP100)} Mt",
              f"×{GWP100} IPCC AR6", delta_color="off")
with k3:
    st.metric(f"CO₂e · GWP20 · {year}", f"{fmt_mt(lfl['total'] * GWP20)} Mt",
              f"×{GWP20} IPCC AR6", delta_color="off")
with k4:
    if len(rr):
        r0 = rr.iloc[0]
        st.metric("World rank", f"#{int(r0['rank_world']):,} of {len(rank):,}",
                  f"#{int(r0['rank_country'])} of {int(r0['n_country'])} in {country}",
                  delta_color="off",
                  help="Rank by methane emitted in the selected year among every subnational "
                       "jurisdiction in this dataset (#1 = largest), and within its country.")
if lfl["is_partial"]:
    st.markdown(
        f'<div class="smac-meta" style="font-size:10px;">⚠ {year} is a partial year — '
        f'{lfl["n_months"]} of 12 months reported. Totals are not comparable to full years.</div>',
        unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============== TREND + SECTOR MIX ==============
ca, cb = st.columns([1.3, 1], gap="large")
with ca:
    eyebrow("Monthly time series")
    st.markdown("<h3>CH₄ tonnes per month</h3>", unsafe_allow_html=True)
    st.plotly_chart(time_series_plotly(gd.admin_monthly(gid), height=300),
                    use_container_width=True, config={"displayModeBar": False})
with cb:
    eyebrow("Sector breakdown")
    st.markdown(f"<h3>{year}</h3>", unsafe_allow_html=True)
    sec = gd.admin_sectors(gid, year)
    if sec.empty:
        st.info("No sector detail for this year.")
    else:
        fig = go.Figure(go.Pie(
            labels=sec["sector"], values=sec["ch4_tonnes"], hole=0.5,
            marker=dict(colors=[SECTOR_COLORS.get(s, "#b9c4bd") for s in sec["sector"]]),
            textinfo="percent", textfont=dict(family="Quicksand, sans-serif", size=11),
        ))
        fig.update_layout(height=300, showlegend=True, margin=dict(l=0, r=0, t=10, b=10),
                          legend=dict(font=dict(size=10, family="Quicksand, sans-serif")),
                          paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

eyebrow("Sector mix over time")
st.plotly_chart(sector_trend_plotly(gd.admin_sector_trend(gid), height=300),
                use_container_width=True, config={"displayModeBar": False})

# ============== TOP 20 FACILITIES ==============
fac, fac_year = gd.admin_facilities(gid, year)
eyebrow("Top emitting sources")
if fac.empty:
    st.info(f"No facility-level sources on file for {loc}.")
else:
    note = "" if fac_year == year else f" (facility data available for {fac_year})"
    st.markdown(f"<h3>Top {len(fac)} methane-emitting facilities · {fac_year}{note}</h3>",
                unsafe_allow_html=True)
    st.markdown(
        '<div class="smac-meta" style="margin-bottom:12px;">individual sites in power, oil &amp; '
        'gas, coal and other mining, manufacturing and waste (e.g. landfills). Oil &amp; gas rows '
        'are often field- or basin-level aggregates. Agriculture, transport and land use are '
        'not site-level in this ranking.</div>',
        unsafe_allow_html=True,
    )
    show = fac.rename(columns={
        "source_name": "Facility", "asset_type": "Type", "sector": "Sector",
        "sub_sector": "Sub-sector", "ch4_tonnes": f"{fac_year} CH₄ (t)",
    })[["Facility", "Type", "Sector", "Sub-sector", f"{fac_year} CH₄ (t)"]]
    st.dataframe(show, hide_index=True, use_container_width=True, height=420,
                 column_config={f"{fac_year} CH₄ (t)": st.column_config.NumberColumn(format="localized")})
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
        f'Working on methane in {loc}?</div>'
        '<div style="font-size:13.5px;line-height:1.6;color:var(--ink-soft);">SMAC members get a '
        'fuller profile — sub-sector detail, a library of peer action plans and policy context — '
        'plus technical and policy support from the coalition. Joining is free.</div></div>',
        unsafe_allow_html=True,
    )
    if st.button("Contact SMAC →", key="gv_contact"):
        st.switch_page("pages/6_Contact.py")

render_footer()
