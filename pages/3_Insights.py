"""
Insights dashboard.
KPIs, time series with period filter, GWP comparison, top emitters, pathway table.
"""

import altair as alt
import pandas as pd
import streamlit as st

from utils.theme import inject_theme, eyebrow
from utils.data_loader import (
    COUNTRY_META, COUNTRY_ORDER, country_monthly,
    location_yearly_ranking, country_yearly, location_monthly, list_locations,
    location_sectors, has_sector_data,
    fmt_int, fmt_mt, pct_change,
)
from utils.policy_content import PATHWAYS, GWP100, GWP20
from utils.charts import (
    time_series_plotly, comparison_plotly, sector_stack_plotly, sector_pies_plotly,
    INK, INK_SOFT, COPPER, MOSS, LINE_SOFT, PAPER,
)


inject_theme()

# ============== HEADER ==============
col_h1, col_h2 = st.columns([2, 1])
with col_h1:
    st.markdown("<h1>Insights <em>dashboard</em></h1>", unsafe_allow_html=True)
    st.markdown('<div class="smac-meta">monthly subnational methane · climate trace 2021–2024</div>',
                unsafe_allow_html=True)
with col_h2:
    if "dash_country" not in st.session_state:
        st.session_state.dash_country = "USA"
    selected = st.selectbox(
        "Country",
        options=COUNTRY_ORDER,
        index=COUNTRY_ORDER.index(st.session_state.dash_country),
        format_func=lambda x: f"{COUNTRY_META[x]['name']} ({x})",
        key="dash_country_select",
    )
    st.session_state.dash_country = selected

iso = st.session_state.dash_country
meta = COUNTRY_META[iso]

st.markdown("<br>", unsafe_allow_html=True)

# ============== KPIs ==============
yearly = country_yearly(iso)
y23 = float(yearly[yearly["year"] == 2023]["ch4_tonnes"].iloc[0]) if 2023 in yearly["year"].values else 0
y24 = float(yearly[yearly["year"] == 2024]["ch4_tonnes"].iloc[0]) if 2024 in yearly["year"].values else 0
yoy = pct_change(y24, y23)

ranking = location_yearly_ranking(iso, year=2024)
total = ranking["ch4_tonnes_year"].sum()
top1 = ranking.iloc[0]
top1_share = top1["share"]

kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.metric("2024 Total CH₄", f"{fmt_mt(y24)} Mt",
              f"{yoy:+.2f}% YoY", delta_color="inverse" if yoy > 0 else "normal")
with kpi_cols[1]:
    st.metric("CO₂e · GWP100", f"{fmt_mt(y24 * GWP100)} Mt", f"×{GWP100} IPCC AR6", delta_color="off")
with kpi_cols[2]:
    st.metric("CO₂e · GWP20", f"{fmt_mt(y24 * GWP20)} Mt", f"×{GWP20} IPCC AR6", delta_color="off")
with kpi_cols[3]:
    st.metric("Top subunit share", f"{top1_share:.1f}%", str(top1["location"]), delta_color="off")

st.markdown("<br>", unsafe_allow_html=True)

# ============== TIME SERIES + GWP ==============
col_t, col_g = st.columns([1.3, 1], gap="large")

with col_t:
    eyebrow("National time series")
    st.markdown("<h3>Monthly CH₄ · tonnes · all subnational units</h3>", unsafe_allow_html=True)
    period = st.radio("Period", options=["All years", "2023–2024"],
                      horizontal=True, key=f"period_{iso}", label_visibility="collapsed")
    monthly = country_monthly(iso)
    if period == "2023–2024":
        monthly = monthly[monthly["year"] >= 2023]
    st.plotly_chart(time_series_plotly(monthly, height=320), use_container_width=True,
                    config={"displayModeBar": False})

with col_g:
    eyebrow("CH₄ vs CO₂e")
    st.markdown("<h3>IPCC AR6 · GWP100 vs GWP20 · 2024</h3>", unsafe_allow_html=True)
    top3 = ranking.head(3)
    st.markdown(
        "<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:var(--ink-soft);"
        "letter-spacing:0.12em;text-transform:uppercase;margin-bottom:14px;'>top 3 subnational units</div>",
        unsafe_allow_html=True,
    )
    for r in top3.itertuples():
        v100 = r.ch4_tonnes_year * GWP100 / 1000
        v20 = r.ch4_tonnes_year * GWP20 / 1000
        st.markdown(
            f"""
            <div style="border-top:1px solid var(--line-soft);padding-top:14px;margin-bottom:14px;">
              <div style="font-family:Fraunces,serif;font-size:18px;margin-bottom:3px;">{r.location}</div>
              <div style="font-family:JetBrains Mono,monospace;font-size:10px;color:var(--ink-soft);letter-spacing:0.1em;margin-bottom:10px;">{fmt_int(r.ch4_tonnes_year)} t CH₄ → CO₂e</div>
              <div style="display:flex;gap:18px;align-items:baseline;">
                <div>
                  <div style="font-family:Fraunces,serif;font-size:28px;font-weight:300;letter-spacing:-0.02em;line-height:1;">{fmt_int(v100)}<span style="font-size:13px;color:var(--ink-soft);">k</span></div>
                  <div style="font-family:JetBrains Mono,monospace;font-size:9px;color:var(--ink-soft);letter-spacing:0.12em;text-transform:uppercase;margin-top:4px;">t · GWP100</div>
                </div>
                <div style="font-family:JetBrains Mono,monospace;color:var(--copper);font-size:14px;">→</div>
                <div>
                  <div style="font-family:Fraunces,serif;font-size:28px;font-weight:300;letter-spacing:-0.02em;line-height:1;color:var(--copper);">{fmt_int(v20)}<span style="font-size:13px;color:var(--ink-soft);">k</span></div>
                  <div style="font-family:JetBrains Mono,monospace;font-size:9px;color:var(--ink-soft);letter-spacing:0.12em;text-transform:uppercase;margin-top:4px;">t · GWP20</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ============== TOP EMITTERS TABLE ==============
eyebrow("Top subnational emitters")
st.markdown("<h3>2024 ranking · share of national CH₄</h3>", unsafe_allow_html=True)

display_df = ranking.head(12).copy()
display_df = display_df[["location", "ch4_tonnes_year", "share", "yoy_pct"]].rename(columns={
    "location": meta["subunit_type"].title(),
    "ch4_tonnes_year": "2024 CH₄ (t)",
    "share": "Share (%)",
    "yoy_pct": "YoY 23→24 (%)",
})

st.dataframe(
    display_df,
    hide_index=True,
    use_container_width=True,
    column_config={
        meta["subunit_type"].title(): st.column_config.TextColumn(width="medium"),
        "2024 CH₄ (t)": st.column_config.NumberColumn(format="%d"),
        "Share (%)": st.column_config.ProgressColumn(
            format="%.2f%%", min_value=0,
            max_value=float(display_df["Share (%)"].max()),
        ),
        "YoY 23→24 (%)": st.column_config.NumberColumn(format="%+.2f%%"),
    },
    height=460,
)

st.markdown("<br>", unsafe_allow_html=True)

# ============== SUBNATIONAL COMPARISON ==============
eyebrow("Subnational comparison")
st.markdown("<h3>Compare regions <em>head-to-head</em></h3>", unsafe_allow_html=True)
st.markdown(
    '<div class="smac-meta" style="margin-bottom:14px;">pick up to 6 subnational units · across any SMAC country</div>',
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def _all_region_options():
    """Map 'Country — Location' label -> (iso, location) for every subnational unit."""
    opts = {}
    for c in COUNTRY_ORDER:
        for loc in list_locations(c):
            opts[f"{COUNTRY_META[c]['name']} — {loc}"] = (c, loc)
    return opts


region_options = _all_region_options()
option_labels = list(region_options.keys())

# Sensible default: top 3 subnational units of the currently selected country
default_labels = [
    f"{meta['name']} — {r.location}"
    for r in ranking.head(3).itertuples()
    if f"{meta['name']} — {r.location}" in region_options
]

cmp_c1, cmp_c2 = st.columns([3, 1])
with cmp_c1:
    selected_labels = st.multiselect(
        "Regions",
        options=option_labels,
        default=default_labels,
        max_selections=6,
        label_visibility="collapsed",
        placeholder="Search and add subnational regions…",
    )
with cmp_c2:
    cmp_metric = st.selectbox(
        "Metric",
        ["CH₄ tonnes", "CO₂e · GWP100", "CO₂e · GWP20"],
        label_visibility="collapsed",
        key="cmp_metric",
    )

factor, unit = {
    "CH₄ tonnes": (1.0, "t CH₄"),
    "CO₂e · GWP100": (float(GWP100), "t CO₂e"),
    "CO₂e · GWP20": (float(GWP20), "t CO₂e"),
}[cmp_metric]

if not selected_labels:
    st.info("Add at least one region above to build the comparison.")
else:
    parts = []
    table_rows = []
    for label in selected_labels:
        c_iso, loc = region_options[label]
        m = location_monthly(c_iso, loc).copy()
        if m.empty:
            continue
        m["value"] = m["ch4_tonnes"] * factor
        m["series"] = loc
        parts.append(m[["date", "value", "series"]])

        y24 = float(m[m["year"] == 2024]["ch4_tonnes"].sum())
        y23 = float(m[m["year"] == 2023]["ch4_tonnes"].sum())
        peak = m.loc[m["ch4_tonnes"].idxmax()]
        table_rows.append({
            "Region": loc,
            "Country": COUNTRY_META[c_iso]["name"],
            "2024 CH₄ (t)": y24,
            "GWP100 CO₂e (t)": y24 * GWP100,
            "GWP20 CO₂e (t)": y24 * GWP20,
            "YoY 23→24 (%)": pct_change(y24, y23),
            "Peak month": peak["date"].strftime("%b %Y"),
        })

    if parts:
        df_long = pd.concat(parts, ignore_index=True)
        st.plotly_chart(
            comparison_plotly(df_long, value_label=cmp_metric, unit=unit, height=360),
            use_container_width=True,
            config={"displayModeBar": False},
        )

        cmp_table = pd.DataFrame(table_rows).sort_values("2024 CH₄ (t)", ascending=False)
        st.dataframe(
            cmp_table,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Region": st.column_config.TextColumn(width="medium"),
                "2024 CH₄ (t)": st.column_config.NumberColumn(format="%d"),
                "GWP100 CO₂e (t)": st.column_config.NumberColumn(format="%d"),
                "GWP20 CO₂e (t)": st.column_config.NumberColumn(format="%d"),
                "YoY 23→24 (%)": st.column_config.NumberColumn(format="%+.2f%%"),
            },
        )

        # ---- sector composition (needs preprocessed SMAC_methane_by_sector.csv) ----
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="smac-struct-label">Sector composition</div>',
                    unsafe_allow_html=True)
        if not has_sector_data():
            st.info(
                "Sector breakdown needs data/SMAC_methane_by_sector.csv. "
                "Run build_sector_data.py once to generate it, then redeploy."
            )
        else:
            sec_c1, sec_c2 = st.columns([1, 1])
            with sec_c1:
                sec_year = st.selectbox("Sector year", [2024, 2023, 2022, 2021],
                                        key="cmp_sec_year", label_visibility="collapsed")
            with sec_c2:
                sec_scale = st.radio("Scale", ["Share %", "Absolute"], horizontal=True,
                                     key="cmp_sec_scale", label_visibility="collapsed")
            sec_parts = []
            for label in selected_labels:
                c_iso, loc = region_options[label]
                s = location_sectors(c_iso, loc, sec_year)
                for r in s.itertuples():
                    sec_parts.append({"region": loc, "sector": r.sector,
                                      "value": float(r.total_emission)})
            if sec_parts:
                sec_df = pd.DataFrame(sec_parts)
                st.plotly_chart(
                    sector_stack_plotly(sec_df, normalize=(sec_scale == "Share %"), height=420),
                    use_container_width=True, config={"displayModeBar": False},
                )
                st.markdown(
                    '<div class="smac-meta" style="margin:10px 0 2px;">composition · share of each region</div>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(
                    sector_pies_plotly(sec_df, height=300),
                    use_container_width=True, config={"displayModeBar": False},
                )
            else:
                st.info("No sector data for the selected regions in that year.")

st.markdown("<br>", unsafe_allow_html=True)

# ============== CROSS-COUNTRY COMPARISON ==============
eyebrow("Cross-country view")
st.markdown("<h3>2024 totals across the SMAC</h3>", unsafe_allow_html=True)

# Build a cross-country dataframe
rows = []
for c in COUNTRY_ORDER:
    cy = country_yearly(c)
    y_now = float(cy[cy["year"] == 2024]["ch4_tonnes"].iloc[0]) if 2024 in cy["year"].values else 0
    y_prev = float(cy[cy["year"] == 2023]["ch4_tonnes"].iloc[0]) if 2023 in cy["year"].values else 0
    rows.append({
        "Country": COUNTRY_META[c]["name"],
        "iso": c,
        "ch4_mt": y_now / 1e6,
        "yoy": pct_change(y_now, y_prev),
    })
cross_df = pd.DataFrame(rows).sort_values("ch4_mt", ascending=False)

bar = alt.Chart(cross_df).mark_bar(height=22).encode(
    y=alt.Y("Country:N", sort="-x",
            axis=alt.Axis(title=None, labelFontSize=12, labelFont="Inter",
                          labelColor=INK)),
    x=alt.X("ch4_mt:Q",
            axis=alt.Axis(title="2024 CH₄ (Mt)", titleFontSize=10,
                          titleFont="JetBrains Mono", titleColor=INK_SOFT,
                          labelFontSize=10, labelFont="JetBrains Mono",
                          labelColor=INK_SOFT, gridColor=LINE_SOFT, gridDash=[2, 2])),
    color=alt.condition(
        f"datum.iso === '{iso}'",
        alt.value(COPPER),
        alt.value(MOSS),
    ),
    tooltip=[
        "Country",
        alt.Tooltip("ch4_mt", format=".2f", title="Mt CH₄"),
        alt.Tooltip("yoy", format="+.2f", title="YoY %"),
    ],
).properties(height=380, background=PAPER).configure_view(strokeWidth=0)

st.altair_chart(bar, use_container_width=True)

st.markdown(
    f"<div class='smac-meta' style='margin-top:-12px;'>highlighted: <strong style='color:var(--copper)'>{meta['name']}</strong></div>",
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ============== PATHWAY TABLE ==============
eyebrow("Policy pathway recommendations")
st.markdown(f"<h3>Mitigation actions for {meta['name']} · with anti-greenwashing flags</h3>",
            unsafe_allow_html=True)

pathways = PATHWAYS.get(iso, [])

# Render as a nicer custom HTML table for the pathway content
table_html = """
<table style="width:100%;border-collapse:collapse;font-family:Inter Tight,sans-serif;border:1px solid var(--line);">
<thead>
<tr>
  <th style="font-family:JetBrains Mono,monospace;font-size:10px;letter-spacing:0.14em;text-transform:uppercase;color:var(--ink-soft);font-weight:500;text-align:left;padding:14px 16px;border-bottom:1.5px solid var(--ink);background:var(--paper-2);">Sector</th>
  <th style="font-family:JetBrains Mono,monospace;font-size:10px;letter-spacing:0.14em;text-transform:uppercase;color:var(--ink-soft);font-weight:500;text-align:left;padding:14px 16px;border-bottom:1.5px solid var(--ink);background:var(--paper-2);">Main issue</th>
  <th style="font-family:JetBrains Mono,monospace;font-size:10px;letter-spacing:0.14em;text-transform:uppercase;color:var(--ink-soft);font-weight:500;text-align:left;padding:14px 16px;border-bottom:1.5px solid var(--ink);background:var(--paper-2);">Mitigation actions</th>
  <th style="font-family:JetBrains Mono,monospace;font-size:10px;letter-spacing:0.14em;text-transform:uppercase;color:var(--ink-soft);font-weight:500;text-align:left;padding:14px 16px;border-bottom:1.5px solid var(--ink);background:var(--paper-2);">Greenwashing flag</th>
</tr>
</thead>
<tbody>
"""

for p in pathways:
    actions_html = "".join(
        f'<span style="font-family:JetBrains Mono,monospace;font-size:10px;padding:4px 9px;background:var(--paper-2);border:1px solid var(--line-soft);letter-spacing:0.04em;display:inline-block;margin:2px 4px 2px 0;">{a}</span>'
        for a in p["actions"]
    )
    table_html += f"""
    <tr>
      <td style="padding:18px 16px;border-bottom:1px solid var(--line-soft);vertical-align:top;font-family:Fraunces,serif;font-size:17px;font-weight:400;width:18%;">{p['sector']}</td>
      <td style="padding:18px 16px;border-bottom:1px solid var(--line-soft);vertical-align:top;font-size:13.5px;line-height:1.55;color:var(--ink-soft);width:24%;">{p['issue']}</td>
      <td style="padding:18px 16px;border-bottom:1px solid var(--line-soft);vertical-align:top;width:34%;">{actions_html}</td>
      <td style="padding:18px 16px;border-bottom:1px solid var(--line-soft);vertical-align:top;font-family:JetBrains Mono,monospace;font-size:11.5px;color:var(--copper);line-height:1.5;">⚠ {p['flag']}</td>
    </tr>
    """

table_html += "</tbody></table>"
# Render with st.html (NOT st.markdown). st.markdown runs content through a
# markdown parser first, and the 4-space-indented <tr>/<td> lines were being
# treated as a code block and shown as raw text. st.html emits HTML directly.
st.html(table_html)
