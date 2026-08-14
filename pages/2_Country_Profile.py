"""
Country / Jurisdiction Profile page.
Country selector, KPIs, time series, sector decomposition, subnational ranking.
"""

import pandas as pd
import streamlit as st

from utils.theme import inject_theme, eyebrow
from utils.data_loader import (
    COUNTRY_META, COUNTRY_ORDER, country_monthly, country_yearly, CURRENT_YEAR, DATA_RANGE_LABEL,
    location_yearly_ranking, member_status, fmt_int, fmt_mt, pct_change,
)
from utils.policy_content import POLICY, SECTORS, GWP100, GWP20
from utils.charts import time_series_plotly, sector_bar_altair, yoy_bar_altair


inject_theme()

# ============== COUNTRY SELECTOR ==============
# Use session state so selection persists across reruns
if "profile_country" not in st.session_state:
    st.session_state.profile_country = "USA"

# Tab-style country picker — a wrapping grid (not one row of 15 too-narrow columns,
# which squeezed "United States" etc. down to one letter per line)
PILLS_PER_ROW = 5
for row_start in range(0, len(COUNTRY_ORDER), PILLS_PER_ROW):
    row_isos = COUNTRY_ORDER[row_start:row_start + PILLS_PER_ROW]
    tab_cols = st.columns(PILLS_PER_ROW)
    for i, iso in enumerate(row_isos):
        with tab_cols[i]:
            is_active = st.session_state.profile_country == iso
            btn_type = "primary" if is_active else "secondary"
            if st.button(COUNTRY_META[iso]["name"], key=f"profile_tab_{iso}",
                         use_container_width=True, type=btn_type):
                st.session_state.profile_country = iso
                st.rerun()

iso = st.session_state.profile_country
meta = COUNTRY_META[iso]
policy = POLICY[iso]
sectors = SECTORS[iso]

st.markdown("<br>", unsafe_allow_html=True)

# ============== HEADER ==============
yearly = country_yearly(iso)
y21 = float(yearly[yearly["year"] == 2021]["ch4_tonnes"].iloc[0]) if 2021 in yearly["year"].values else 0
y_prior = float(yearly[yearly["year"] == CURRENT_YEAR - 1]["ch4_tonnes"].iloc[0]) if (CURRENT_YEAR - 1) in yearly["year"].values else 0
y_now = float(yearly[yearly["year"] == CURRENT_YEAR]["ch4_tonnes"].iloc[0]) if CURRENT_YEAR in yearly["year"].values else 0
yoy = pct_change(y_now, y_prior)
drift = pct_change(y_now, y21)

ranking = location_yearly_ranking(iso, year=CURRENT_YEAR)
n_loc = len(ranking)

if ranking.empty:
    st.markdown(
        f'<div class="smac-meta">{meta["region"]} &nbsp; · &nbsp; new SMAC member</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"<h1 style='font-size:4rem;margin-top:8px;margin-bottom:18px;'>{meta['name']}</h1>",
                unsafe_allow_html=True)
    st.info(
        f"**{meta['name']}** is a recent addition to SMAC's membership. Climate TRACE "
        f"emissions data for it hasn't been loaded into this tool yet — it's coming soon. "
        f"Pick a different country above to explore data that's already loaded.",
        icon="🌱",
    )
    st.stop()

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown(
        f'<div class="smac-meta">{meta["region"]} &nbsp; · &nbsp; {n_loc} SMAC {meta["subunit_type"]}{"s" if n_loc != 1 else ""} &nbsp; · &nbsp; {DATA_RANGE_LABEL}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<h1 style='font-size:4rem;margin-top:8px;margin-bottom:18px;'>{meta['name']}</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="font-family:Quicksand,sans-serif;font-size:18px;line-height:1.6;color:var(--ink-soft);font-weight:300;">{policy["summary"]}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<a href="https://climatetrace.org/explore?search={meta["name"].replace(" ", "+")}" '
        f'target="_blank" style="text-decoration:none;">'
        f'<span class="smac-pill">🗺 View {meta["name"]} source map on Climate TRACE →</span></a>',
        unsafe_allow_html=True,
    )
    with st.expander(f"Show map of {meta['name']}"):
        import streamlit.components.v1 as components
        components.iframe(
            f"https://www.google.com/maps?q={meta['name'].replace(' ', '+')}&output=embed",
            height=220,
        )
        st.markdown(
            '<div class="smac-meta" style="font-size:9px;margin-top:6px;line-height:1.5;">'
            'General-location map for orientation. For facility-level emission sources, use '
            'the Climate TRACE link above.</div>',
            unsafe_allow_html=True,
        )

with col2:
    st.markdown(
        f"""
        <div style="border-left:1px solid var(--line);padding-left:28px;height:100%;">
          <div style="font-family:Quicksand,sans-serif;font-size:10px;letter-spacing:0.16em;text-transform:uppercase;color:var(--copper);margin-bottom:10px;">/ Governance</div>
          <p style="font-size:14px;line-height:1.65;color:var(--ink-soft);margin-bottom:6px;">{policy['governance']}</p>
          <p style="font-size:11px;line-height:1.5;color:var(--ink-soft);opacity:0.75;margin-bottom:18px;">National structure, for context — the data and charts on this page cover only {n_loc} SMAC {meta['subunit_type']}{'s' if n_loc != 1 else ''}, not every {meta['subunit_type']} shown above.</p>
          <div style="font-family:Quicksand,sans-serif;font-size:10px;letter-spacing:0.16em;text-transform:uppercase;color:var(--copper);margin-bottom:10px;">/ Key policy instruments</div>
          {''.join(f'<p style="font-size:14px;line-height:1.65;color:var(--ink-soft);margin-bottom:14px;"><strong style="color:var(--ink);">{n}.</strong> {d}</p>' for n, d in policy['policies'])}
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============== KPIs ==============
kpi_cols = st.columns(4)
with kpi_cols[0]:
    delta_text = f"{yoy:+.2f}% YoY"
    delta_color = "inverse" if yoy > 0 else "normal"
    st.metric(f"{CURRENT_YEAR} Total CH₄", f"{fmt_mt(y_now)} Mt", delta_text, delta_color=delta_color)
with kpi_cols[1]:
    st.metric("CO₂e · GWP100", f"{fmt_mt(y_now * GWP100)} Mt", f"×{GWP100} (IPCC AR6)", delta_color="off")
with kpi_cols[2]:
    st.metric("CO₂e · GWP20", f"{fmt_mt(y_now * GWP20)} Mt", f"×{GWP20} (IPCC AR6)", delta_color="off")
with kpi_cols[3]:
    delta_color = "inverse" if drift > 0 else "normal"
    st.metric(f"{CURRENT_YEAR - 2021}-year drift", f"{drift:+.1f}%", f"2021 → {CURRENT_YEAR}", delta_color=delta_color)

st.markdown("<br>", unsafe_allow_html=True)

# ============== TIME SERIES + SECTORS ==============
col_a, col_b = st.columns([1.3, 1], gap="large")

with col_a:
    eyebrow("Monthly time series")
    st.markdown(f"<h3>CH₄ tonnes · all SMAC subnational units · {DATA_RANGE_LABEL}</h3>", unsafe_allow_html=True)
    monthly = country_monthly(iso)
    st.plotly_chart(time_series_plotly(monthly, height=320), use_container_width=True,
                    config={"displayModeBar": False})

with col_b:
    eyebrow("Sector decomposition")
    st.markdown("<h3>Approximate · literature-derived</h3>", unsafe_allow_html=True)
    st.altair_chart(sector_bar_altair(sectors, height=320), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============== SUBNATIONAL RANKING ==============
prior_yy, now_yy = str(CURRENT_YEAR - 1)[2:], str(CURRENT_YEAR)[2:]
eyebrow(f"Subnational ranking · {CURRENT_YEAR}")
st.markdown("<h3>Top emitters and year-over-year movement</h3>", unsafe_allow_html=True)

display_df = ranking.head(15).copy()
display_df["SMAC Status"] = display_df["location"].apply(
    lambda loc: {"member": "● Member", "observer": "○ Observer"}.get(member_status(iso, loc), "")
)
display_df = display_df.rename(columns={
    "location": meta["subunit_type"].title(),
    "ch4_tonnes_year": f"{CURRENT_YEAR} CH₄ (t)",
    "share": "Share (%)",
    "yoy_pct": f"YoY {prior_yy}→{now_yy} (%)",
})

# Configure column display
col_config = {
    meta["subunit_type"].title(): st.column_config.TextColumn(width="medium"),
    "SMAC Status": st.column_config.TextColumn(width="small"),
    f"{CURRENT_YEAR} CH₄ (t)": st.column_config.NumberColumn(format="%d"),
    "Share (%)": st.column_config.ProgressColumn(
        format="%.2f%%", min_value=0,
        max_value=float(display_df["Share (%)"].max()) if len(display_df) else 1.0,
    ),
    f"YoY {prior_yy}→{now_yy} (%)": st.column_config.NumberColumn(format="%+.2f%%"),
}

# Drop the underlying yearly raw columns we don't need
keep_cols = [meta["subunit_type"].title(), "SMAC Status", f"{CURRENT_YEAR} CH₄ (t)", "Share (%)", f"YoY {prior_yy}→{now_yy} (%)"]
display_df = display_df[keep_cols]

st.dataframe(display_df, hide_index=True, use_container_width=True,
             column_config=col_config, height=560)
st.markdown(
    '<div class="smac-meta" style="font-size:11px;margin-top:8px;">'
    '● Member = full SMAC member &nbsp;·&nbsp; ○ Observer = SMAC observer</div>',
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ============== YoY visual ==============
col_y1, col_y2 = st.columns([1, 1], gap="large")
with col_y1:
    eyebrow("Year-over-year change")
    st.markdown(f"<h3>Top 10 movers · {CURRENT_YEAR - 1} → {CURRENT_YEAR}</h3>", unsafe_allow_html=True)
    yoy_df = ranking.head(10).copy()
    if "yoy_pct" in yoy_df.columns:
        yoy_df = yoy_df.dropna(subset=["yoy_pct"])
        st.altair_chart(yoy_bar_altair(yoy_df, height=320), use_container_width=True)

with col_y2:
    eyebrow("Concentration")
    st.markdown("<h3>How concentrated is the country's methane?</h3>", unsafe_allow_html=True)
    cumulative = ranking.head(10).copy()
    cumulative["cum_share"] = cumulative["share"].cumsum()
    cumulative["rank"] = range(1, len(cumulative) + 1)
    cumulative_chart = pd.DataFrame({
        "rank": cumulative["rank"],
        "cum_share": cumulative["cum_share"],
        "location": cumulative["location"],
    })

    import altair as alt
    from utils.charts import MOSS, COPPER, INK_SOFT, LINE_SOFT, PAPER, INK
    line = alt.Chart(cumulative_chart).mark_line(color=MOSS, strokeWidth=2.4, point=alt.OverlayMarkDef(filled=True, fill=MOSS, size=70)).encode(
        x=alt.X("rank:Q", title=f"Top N {meta['subunit_type']}s",
                scale=alt.Scale(domain=[1, 10]),
                axis=alt.Axis(titleFontSize=10, titleFont="Quicksand", titleColor=INK_SOFT,
                              labelFontSize=10, labelFont="Quicksand", labelColor=INK_SOFT,
                              gridColor=LINE_SOFT, gridDash=[2, 2], values=list(range(1, 11)))),
        y=alt.Y("cum_share:Q", title="Cumulative share (%)",
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(titleFontSize=10, titleFont="Quicksand", titleColor=INK_SOFT,
                              labelFontSize=10, labelFont="Quicksand", labelColor=INK_SOFT,
                              gridColor=LINE_SOFT, gridDash=[2, 2])),
        tooltip=["rank", "location", alt.Tooltip("cum_share", format=".1f", title="Cumulative %")],
    ).properties(height=320, background=PAPER).configure_view(strokeWidth=0)
    st.altair_chart(line, use_container_width=True)
