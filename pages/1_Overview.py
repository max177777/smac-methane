"""
Overview / landing page.
"""

import streamlit as st

from utils.theme import inject_theme, eyebrow, dot_logo, dark_band
from utils.data_loader import (
    COUNTRY_META, COUNTRY_ORDER, all_countries_year_total, CURRENT_YEAR, DATA_RANGE_LABEL,
    MEMBER_ROSTER, total_member_counts, total_months_of_data,
    country_monthly, country_yearly, fmt_mt, pct_change,
)
from utils.charts import sparkline_plotly


inject_theme()

# ============== HERO ==============
col1, col2 = st.columns([1.4, 1], gap="large")

with col1:
    dot_logo(36)
    eyebrow("AI Methane Decision Assistant · V1")
    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;margin:-4px 0 18px;flex-wrap:wrap;">'
        '<span class="smac-pill">● Prototype</span>'
        f'<span class="smac-meta" style="font-size:12px;">Climate TRACE · {DATA_RANGE_LABEL}</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h1 style='margin-bottom:0;'>Translating <em>methane data</em> into "
        "policy actions.</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="font-family:Inter,sans-serif;font-size:18px;line-height:1.6;'
        'color:var(--ink-soft);max-width:520px;margin-top:24px;font-weight:400;">'
        "An AI-assisted reasoning interface for subnational governments and organizations, "
        "integrating 48 months of methane emissions data across all SMAC members — over 300 "
        "subnational units — paired with a chat that reasons through IPCC GWP frameworks and "
        "policy context."
        "</p>",
        unsafe_allow_html=True,
    )

    st.write("")
    cta1, cta2, cta3 = st.columns([1, 1, 1])
    with cta1:
        if st.button("Open Chat →", use_container_width=True, type="primary"):
            st.switch_page("pages/4_Chat.py")
    with cta2:
        if st.button("The SMAC Group →", use_container_width=True, type="secondary"):
            st.switch_page("pages/2_Country_Profile.py")
    with cta3:
        if st.button("Data & Methods →", use_container_width=True, type="secondary"):
            st.switch_page("pages/5_Data_Methods.py")
    st.markdown(
        '<div class="smac-meta" style="font-size:10px;margin-top:10px;">'
        'New here? Start with <strong>Data &amp; Methods</strong> — what this data is, '
        'and where it falls short.</div>',
        unsafe_allow_html=True,
    )

with col2:
    summary = all_countries_year_total(CURRENT_YEAR)
    total_now = summary["ch4_year_tonnes"].sum()
    total_loc = int(summary["n_locations"].sum())
    n_months = total_months_of_data()

    eyebrow(f"At a glance · {CURRENT_YEAR}")
    st.markdown(
        f"""
        <div style="border-top:1px solid var(--line);padding:20px 0;display:flex;justify-content:space-between;align-items:baseline;">
          <div style="font-family:Quicksand,sans-serif;font-size:42px;font-weight:300;letter-spacing:-0.02em;line-height:1;">
            {len(COUNTRY_ORDER)}<span style="font-family:Quicksand,sans-serif;font-size:11px;color:var(--ink-soft);margin-left:6px;letter-spacing:0.1em;">countries</span>
          </div>
          <div style="font-family:Quicksand,sans-serif;font-size:10px;text-transform:uppercase;letter-spacing:0.12em;color:var(--ink-soft);text-align:right;max-width:180px;line-height:1.4;">SMAC MEMBERS &amp; OBSERVERS</div>
        </div>
        <div style="border-top:1px solid var(--line);padding:20px 0;display:flex;justify-content:space-between;align-items:baseline;">
          <div style="font-family:Quicksand,sans-serif;font-size:42px;font-weight:300;letter-spacing:-0.02em;line-height:1;">
            {total_loc}<span style="font-family:Quicksand,sans-serif;font-size:11px;color:var(--ink-soft);margin-left:6px;letter-spacing:0.1em;">subnational jurisdictions</span>
          </div>
          <div style="font-family:Quicksand,sans-serif;font-size:10px;text-transform:uppercase;letter-spacing:0.12em;color:var(--ink-soft);text-align:right;max-width:180px;line-height:1.4;">Actual SMAC members &amp; observers</div>
        </div>
        <div style="border-top:1px solid var(--line);padding:20px 0;display:flex;justify-content:space-between;align-items:baseline;">
          <div style="font-family:Quicksand,sans-serif;font-size:42px;font-weight:300;letter-spacing:-0.02em;line-height:1;">
            {n_months}<span style="font-family:Quicksand,sans-serif;font-size:11px;color:var(--ink-soft);margin-left:6px;letter-spacing:0.1em;">months</span>
          </div>
          <div style="font-family:Quicksand,sans-serif;font-size:10px;text-transform:uppercase;letter-spacing:0.12em;color:var(--ink-soft);text-align:right;max-width:180px;line-height:1.4;">Monthly time series · {DATA_RANGE_LABEL}</div>
        </div>
        <div style="border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:20px 0;display:flex;justify-content:space-between;align-items:baseline;">
          <div style="font-family:Quicksand,sans-serif;font-size:42px;font-weight:300;letter-spacing:-0.02em;line-height:1;">
            {fmt_mt(total_now)}<span style="font-family:Quicksand,sans-serif;font-size:11px;color:var(--ink-soft);margin-left:6px;letter-spacing:0.1em;">Mt CH₄</span>
          </div>
          <div style="font-family:Quicksand,sans-serif;font-size:10px;text-transform:uppercase;letter-spacing:0.12em;color:var(--ink-soft);text-align:right;max-width:180px;line-height:1.4;">Combined {CURRENT_YEAR} SMAC emissions</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ============== MEMBERS ==============
n_members, n_observers = total_member_counts()
eyebrow("Members")
st.markdown(
    f"<h2 style='font-size:2.2rem;margin-bottom:8px;'>{n_members} members "
    f"<em>and {n_observers} observers</em>, across {len(COUNTRY_ORDER)} countries.</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    '<p style="color:var(--ink-soft);font-size:14px;margin-bottom:28px;">'
    "Every jurisdiction below is an actual SMAC member or observer — not just any state "
    "or province Climate TRACE happens to publish data for."
    "</p>",
    unsafe_allow_html=True,
)

REGION_GROUPS = [
    ["Africa", "Asia"],
    ["Europe", "North America"],
    ["South America"],
]
region_to_isos: dict[str, list[str]] = {}
for _iso in COUNTRY_ORDER:
    region_to_isos.setdefault(COUNTRY_META[_iso]["region"], []).append(_iso)

member_cols = st.columns(3, gap="large")
for col, regions in zip(member_cols, REGION_GROUPS):
    with col:
        for region in regions:
            st.markdown(
                f'<div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:15px;'
                f'margin:4px 0 10px;">{region}</div>',
                unsafe_allow_html=True,
            )
            for iso in region_to_isos.get(region, []):
                for row in MEMBER_ROSTER.get(iso, []):
                    tag = ("  <span style='color:var(--ink-soft);'>(Observer)</span>"
                           if row["status"] == "observer" else "")
                    st.markdown(
                        f'<div style="font-size:13.5px;line-height:1.9;color:var(--ink);">'
                        f'{row["location"]}, {COUNTRY_META[iso]["name"]}{tag}</div>',
                        unsafe_allow_html=True,
                    )
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

with dark_band():
    eyebrow("Methodology")
    st.markdown("<h2 style='font-size:2.2rem;margin-bottom:32px;'>Five-stage <em>reasoning pipeline</em>.</h2>", unsafe_allow_html=True)

    flow_steps = [
        ("01 / DATA", "Load", "Monthly methane data from Climate TRACE across SMAC countries, down to subnational units."),
        ("02 / CLEAN", "Check", "Validate time trends, detect unusual changes, and flag uncertainty at the local level."),
        ("03 / INSIGHT", "Translate", "Convert CH₄ into CO₂e using IPCC GWP100 and GWP20, and identify emission hotspots."),
        ("04 / DECISION", "Reason", "AI chat connects data with policy context and explains what is happening and why."),
        ("05 / ACTION", "Recommend", "Suggest mitigation pathways based on impact, while flagging potential greenwashing risks."),
    ]
    flow_cols = st.columns(5)
    for i, (num, title, desc) in enumerate(flow_steps):
        with flow_cols[i]:
            is_last = i == len(flow_steps) - 1
            bg = "var(--mint)" if is_last else "rgba(255,255,255,0.06)"
            text_color = "var(--ink)" if is_last else "#ffffff"
            soft_color = "var(--ink)" if is_last else "rgba(255,255,255,0.65)"
            border_color = "transparent" if is_last else "rgba(255,255,255,0.14)"
            st.markdown(
                f"""
                <div style="padding:24px 18px;background:{bg};border:1px solid {border_color};border-radius:14px;height:100%;color:{text_color};">
                  <div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:11px;color:{soft_color};letter-spacing:0.1em;margin-bottom:10px;">{num}</div>
                  <div style="font-family:Quicksand,sans-serif;font-size:22px;font-weight:700;letter-spacing:-0.01em;margin-bottom:6px;">{title}</div>
                  <div style="font-size:12.5px;line-height:1.5;color:{soft_color};">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ============== COUNTRY GRID ==============
eyebrow("THE SMAC")
st.markdown(
    f"<h2 style='font-size:2.2rem;margin-bottom:32px;'>{len(COUNTRY_ORDER)} countries, "
    f"<em>distinct policy textures.</em></h2>",
    unsafe_allow_html=True,
)

# Build a 3-column responsive grid
cols_per_row = 3
year_totals = all_countries_year_total(CURRENT_YEAR)
for row_start in range(0, len(COUNTRY_ORDER), cols_per_row):
    cols = st.columns(cols_per_row, gap="small")
    for j, iso in enumerate(COUNTRY_ORDER[row_start:row_start + cols_per_row]):
        with cols[j]:
            meta = COUNTRY_META[iso]

            yearly = country_yearly(iso)
            y_prior = float(yearly[yearly["year"] == CURRENT_YEAR - 1]["ch4_tonnes"].iloc[0]) if (CURRENT_YEAR - 1) in yearly["year"].values else 0
            y_now = float(yearly[yearly["year"] == CURRENT_YEAR]["ch4_tonnes"].iloc[0]) if CURRENT_YEAR in yearly["year"].values else 0
            yoy = pct_change(y_now, y_prior)
            n_loc = int(year_totals.query(f"iso3 == '{iso}'")["n_locations"].iloc[0])
            arrow = "↑" if yoy > 0.5 else ("↓" if yoy < -0.5 else "→")
            arrow_color = "var(--warn)" if yoy > 0.5 else ("var(--good)" if yoy < -0.5 else "var(--ink-soft)")

            st.markdown(
                f"""
                <div style="border:1px solid var(--line);padding:24px 22px;background:var(--paper);height:100%;">
                  <div style="font-family:Quicksand,sans-serif;font-size:10px;color:var(--ink-soft);letter-spacing:0.16em;display:flex;justify-content:space-between;margin-bottom:14px;">
                    <span>{meta['region'].upper()}</span><span>ISO · {iso}</span>
                  </div>
                  <div style="font-family:Quicksand,sans-serif;font-size:30px;font-weight:400;letter-spacing:-0.02em;line-height:1;margin-bottom:4px;">{meta['name']}</div>
                  <div style="font-family:Inter,sans-serif;font-size:12px;color:var(--ink-soft);margin-bottom:18px;">{n_loc} SMAC {meta['subunit_type']}{'s' if n_loc != 1 else ''}</div>
                  <div style="display:flex;flex-direction:column;gap:6px;margin-bottom:14px;">
                    <div style="display:flex;justify-content:space-between;border-bottom:1px dotted var(--line-soft);padding-bottom:5px;font-size:12px;">
                      <span style="color:var(--ink-soft);font-family:Quicksand,sans-serif;font-size:10px;letter-spacing:0.08em;text-transform:uppercase;">{CURRENT_YEAR} total</span>
                      <span style="font-family:Quicksand,sans-serif;font-weight:500;">{fmt_mt(y_now)} Mt CH₄</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;border-bottom:1px dotted var(--line-soft);padding-bottom:5px;font-size:12px;">
                      <span style="color:var(--ink-soft);font-family:Quicksand,sans-serif;font-size:10px;letter-spacing:0.08em;text-transform:uppercase;">YoY {str(CURRENT_YEAR - 1)[2:]}→{str(CURRENT_YEAR)[2:]}</span>
                      <span style="font-family:Quicksand,sans-serif;font-weight:500;color:{arrow_color};">{arrow} {yoy:+.2f}%</span>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Sparkline
            monthly = country_monthly(iso)
            st.plotly_chart(sparkline_plotly(monthly, height=50), use_container_width=True,
                            config={"displayModeBar": False})

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    '<div style="text-align:center;font-family:Quicksand,sans-serif;font-size:10px;color:var(--ink-soft);letter-spacing:0.14em;text-transform:uppercase;padding:24px 0;border-top:1px solid var(--line);">'
    f'smac prototype <span style="color:var(--copper);">✦</span> climate trace data · {DATA_RANGE_LABEL} <span style="color:var(--copper);">✦</span> TESTING '
    '</div>',
    unsafe_allow_html=True,
)
