"""
Overview / landing page.
"""

import streamlit as st

from utils.theme import inject_theme, eyebrow
from utils.data_loader import (
    COUNTRY_META, COUNTRY_ORDER, all_countries_2024_total,
    country_monthly, country_yearly, fmt_mt, pct_change,
)
from utils.charts import sparkline_plotly


inject_theme()

# ============== HERO ==============
col1, col2 = st.columns([1.4, 1], gap="large")

with col1:
    eyebrow("AI Methane Decision Assistant · V1")
    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;margin:-4px 0 18px;flex-wrap:wrap;">'
        '<span class="smac-pill" style="color:var(--copper);border-color:var(--copper);">● Prototype</span>'
        '<span class="smac-meta" style="font-size:10px;">Climate TRACE · 2021–2024</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h1 style='margin-bottom:0;'>Translating <em>methane data</em> into "
        "<span style='color:var(--copper);font-style:italic;'>policy actions.</span></h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="font-family:Fraunces,serif;font-size:18px;line-height:1.6;'
        'color:var(--ink-soft);max-width:520px;margin-top:24px;font-weight:300;">'
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
            st.switch_page("pages/2_Atlas.py")
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
    summary = all_countries_2024_total()
    total_2024 = summary["ch4_2024_tonnes"].sum()
    total_loc = int(summary["n_locations"].sum())

    eyebrow("At a glance · 2024")
    st.markdown(
        f"""
        <div style="border-top:1px solid var(--line);padding:20px 0;display:flex;justify-content:space-between;align-items:baseline;">
          <div style="font-family:Fraunces,serif;font-size:42px;font-weight:300;letter-spacing:-0.02em;line-height:1;">
            {len(COUNTRY_ORDER)}<span style="font-family:JetBrains Mono,monospace;font-size:11px;color:var(--ink-soft);margin-left:6px;letter-spacing:0.1em;">countries (More coming soon)</span>
          </div>
          <div style="font-family:JetBrains Mono,monospace;font-size:10px;text-transform:uppercase;letter-spacing:0.12em;color:var(--ink-soft);text-align:right;max-width:180px;line-height:1.4;">FROM SMAC MEMBERS</div>
        </div>
        <div style="border-top:1px solid var(--line);padding:20px 0;display:flex;justify-content:space-between;align-items:baseline;">
          <div style="font-family:Fraunces,serif;font-size:42px;font-weight:300;letter-spacing:-0.02em;line-height:1;">
            {total_loc}<span style="font-family:JetBrains Mono,monospace;font-size:11px;color:var(--ink-soft);margin-left:6px;letter-spacing:0.1em;">subnational locations</span>
          </div>
          <div style="font-family:JetBrains Mono,monospace;font-size:10px;text-transform:uppercase;letter-spacing:0.12em;color:var(--ink-soft);text-align:right;max-width:180px;line-height:1.4;">States, provinces, autonomous regions</div>
        </div>
        <div style="border-top:1px solid var(--line);padding:20px 0;display:flex;justify-content:space-between;align-items:baseline;">
          <div style="font-family:Fraunces,serif;font-size:42px;font-weight:300;letter-spacing:-0.02em;line-height:1;">
            48<span style="font-family:JetBrains Mono,monospace;font-size:11px;color:var(--ink-soft);margin-left:6px;letter-spacing:0.1em;">months</span>
          </div>
          <div style="font-family:JetBrains Mono,monospace;font-size:10px;text-transform:uppercase;letter-spacing:0.12em;color:var(--ink-soft);text-align:right;max-width:180px;line-height:1.4;">Monthly time series · 2021 to 2024</div>
        </div>
        <div style="border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:20px 0;display:flex;justify-content:space-between;align-items:baseline;">
          <div style="font-family:Fraunces,serif;font-size:42px;font-weight:300;letter-spacing:-0.02em;line-height:1;">
            {fmt_mt(total_2024)}<span style="font-family:JetBrains Mono,monospace;font-size:11px;color:var(--ink-soft);margin-left:6px;letter-spacing:0.1em;">Mt CH₄</span>
          </div>
          <div style="font-family:JetBrains Mono,monospace;font-size:10px;text-transform:uppercase;letter-spacing:0.12em;color:var(--ink-soft);text-align:right;max-width:180px;line-height:1.4;">Combined 2024 SMAC emissions</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ============== WORKFLOW ==============
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
        bg = "var(--moss)" if is_last else "var(--paper-2)"
        text_color = "var(--paper)" if is_last else "var(--ink)"
        soft_color = "var(--paper)" if is_last else "var(--ink-soft)"
        st.markdown(
            f"""
            <div style="padding:24px 18px;background:{bg};border:1px solid var(--line);height:100%;color:{text_color};">
              <div style="font-family:JetBrains Mono,monospace;font-size:10px;color:{soft_color};letter-spacing:0.14em;margin-bottom:10px;">{num}</div>
              <div style="font-family:Fraunces,serif;font-size:22px;font-weight:400;letter-spacing:-0.01em;margin-bottom:6px;">{title}</div>
              <div style="font-size:12px;line-height:1.5;color:{soft_color};">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ============== COUNTRY GRID ==============
eyebrow("THE SMAC")
st.markdown("<h2 style='font-size:2.2rem;margin-bottom:32px;'>Eleven countries (More updates coming soon), <em>distinct policy textures.</em></h2>", unsafe_allow_html=True)

# Build a 3-column responsive grid
cols_per_row = 3
for row_start in range(0, len(COUNTRY_ORDER), cols_per_row):
    cols = st.columns(cols_per_row, gap="small")
    for j, iso in enumerate(COUNTRY_ORDER[row_start:row_start + cols_per_row]):
        with cols[j]:
            meta = COUNTRY_META[iso]
            yearly = country_yearly(iso)
            y23 = float(yearly[yearly["year"] == 2023]["ch4_tonnes"].iloc[0]) if 2023 in yearly["year"].values else 0
            y24 = float(yearly[yearly["year"] == 2024]["ch4_tonnes"].iloc[0]) if 2024 in yearly["year"].values else 0
            yoy = pct_change(y24, y23)
            n_loc = (all_countries_2024_total().query(f"iso3 == '{iso}'")["n_locations"].iloc[0])
            arrow = "↑" if yoy > 0.5 else ("↓" if yoy < -0.5 else "→")
            arrow_color = "var(--copper)" if yoy > 0.5 else ("var(--good)" if yoy < -0.5 else "var(--ink-soft)")

            st.markdown(
                f"""
                <div style="border:1px solid var(--line);padding:24px 22px;background:var(--paper);height:100%;">
                  <div style="font-family:JetBrains Mono,monospace;font-size:10px;color:var(--ink-soft);letter-spacing:0.16em;display:flex;justify-content:space-between;margin-bottom:14px;">
                    <span>{meta['region'].upper()}</span><span>ISO · {iso}</span>
                  </div>
                  <div style="font-family:Fraunces,serif;font-size:30px;font-weight:400;letter-spacing:-0.02em;line-height:1;margin-bottom:4px;">{meta['name']}</div>
                  <div style="font-family:Inter Tight,sans-serif;font-size:12px;color:var(--ink-soft);margin-bottom:18px;">Federal + {n_loc} {meta['subunit_type']}{'s' if n_loc > 1 else ''}</div>
                  <div style="display:flex;flex-direction:column;gap:6px;margin-bottom:14px;">
                    <div style="display:flex;justify-content:space-between;border-bottom:1px dotted var(--line-soft);padding-bottom:5px;font-size:12px;">
                      <span style="color:var(--ink-soft);font-family:JetBrains Mono,monospace;font-size:10px;letter-spacing:0.08em;text-transform:uppercase;">2024 total</span>
                      <span style="font-family:JetBrains Mono,monospace;font-weight:500;">{fmt_mt(y24)} Mt CH₄</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;border-bottom:1px dotted var(--line-soft);padding-bottom:5px;font-size:12px;">
                      <span style="color:var(--ink-soft);font-family:JetBrains Mono,monospace;font-size:10px;letter-spacing:0.08em;text-transform:uppercase;">YoY 23→24</span>
                      <span style="font-family:JetBrains Mono,monospace;font-weight:500;color:{arrow_color};">{arrow} {yoy:+.2f}%</span>
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
    '<div style="text-align:center;font-family:JetBrains Mono,monospace;font-size:10px;color:var(--ink-soft);letter-spacing:0.14em;text-transform:uppercase;padding:24px 0;border-top:1px solid var(--line);">'
    'smac prototype <span style="color:var(--copper);">✦</span> climate trace data · 2021–2024 <span style="color:var(--copper);">✦</span> TESTING '
    '</div>',
    unsafe_allow_html=True,
)
