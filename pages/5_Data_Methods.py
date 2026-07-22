"""
Data & Methods page.
An explicit, plain-language explanation of what data powers this tool, where it
comes from, what it's good for, and where it falls short. Exists so nobody reads
a number here as more certain than it actually is.
"""

import streamlit as st

from utils.theme import inject_theme, eyebrow


inject_theme()

# ============== HERO ==============
eyebrow("Data & Methods")
st.markdown(
    "<h1 style='margin-bottom:18px;'>What this tool is — "
    "<em>and isn't.</em></h1>",
    unsafe_allow_html=True,
)
st.markdown(
    '<p style="font-family:Fraunces,serif;font-size:19px;line-height:1.65;'
    'color:var(--ink-soft);max-width:760px;font-weight:300;">'
    "This tool exists to give SMAC members a fast, first-pass read on <strong>where their "
    "methane comes from</strong>. Concretely, we are trying to do one thing well: get a "
    "basic sense of the <strong>sources and sectors</strong> of methane emissions by "
    "jurisdiction, with a clearer sense of the <strong>major emitters</strong> — enough to "
    "point a government toward where a real <strong>action plan</strong> is worth building. "
    "It is not a regulatory-grade monitoring system, a substitute for a certified inventory, "
    "or a live sensor feed."
    "</p>",
    unsafe_allow_html=True,
)

st.markdown("---")

# ============== WHERE THE DATA COMES FROM ==============
eyebrow("Where the data comes from")
st.markdown(
    "<h2>Climate TRACE — modeled, not measured directly.</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    '<p style="font-size:15px;line-height:1.7;color:var(--ink-soft);max-width:760px;">'
    "Climate TRACE is an independent, nonprofit coalition (satellite operators, universities, "
    "and research labs) that estimates greenhouse gas emissions for essentially every country, "
    "state/province, and more than 660 million individual facilities and assets worldwide. It "
    "does this by combining satellite imagery, remote sensors, and activity data (production "
    "volumes, land-use change, livestock counts, and similar) with sector-specific emissions "
    "models — it is <strong>inference from indirect signals</strong>, not a network of "
    "continuous ground-truth methane monitors."
    "</p>"
    '<p style="font-size:15px;line-height:1.7;color:var(--ink-soft);max-width:760px;">'
    "As of March 2025, Climate TRACE releases a new month of data every month, with roughly a "
    "60-day lag — so the most recent month you can see here is never truly current, and each "
    "release also revises prior months as better information comes in."
    "</p>",
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ============== LIMITATIONS ==============
eyebrow("Known limitations")
st.markdown(
    "<h2>Read the numbers with these caveats in mind.</h2>",
    unsafe_allow_html=True,
)

limitations = [
    ("Modeled, not monitored",
     "Every figure is a model output built from satellite and sensor signals plus activity "
     "data — not a direct, continuous measurement of methane in the air. Treat it as a "
     "well-informed estimate, not a metered reading."),
    ("Satellites capture moments, not a continuous feed",
     "A satellite passes over any given facility or region only periodically — a handful of "
     "overpasses a month, not continuous coverage. Climate TRACE's models stitch these "
     "point-in-time observations together with activity data to estimate a monthly total, but "
     "the underlying satellite signal is a series of snapshots, not an uninterrupted stream of "
     "emissions data. A short-lived spike or lull between overpasses can be missed entirely."),
    ("~60-day reporting lag, and revisions",
     "The newest month available is always about two months old, and Climate TRACE "
     "regularly revises earlier months (sometimes years back) as methods improve. A number "
     "you see today may shift slightly in a future release."),
    ("Uncertainty varies a lot by sector",
     "Large point sources like oil & gas facilities and power plants are estimated with "
     "tighter confidence. Diffuse sources — small-scale agriculture, informal waste sites, "
     "land-use change — carry wider uncertainty bands, sometimes ±25% or more at the "
     "subnational level."),
    ("Subnational split is itself modeled",
     "Attribution of national totals down to states, provinces, or other subnational units "
     "is a modeled allocation based on asset locations and administrative boundaries — not "
     "a jurisdiction's own self-report or a government-certified inventory."),
    ("A snapshot of modeled totals, not a live feed",
     "Because releases happen monthly with a lag, what you're looking at is closer to a "
     "periodic snapshot of the model's best current estimate than to continuous real-time "
     "emissions tracking."),
]

for title, desc in limitations:
    st.markdown(
        f"""
        <div style="border-left:3px solid var(--copper);padding:4px 20px;margin-bottom:20px;">
          <div style="font-family:Fraunces,serif;font-size:19px;font-weight:400;margin-bottom:6px;">{title}</div>
          <div style="font-size:14px;line-height:1.65;color:var(--ink-soft);max-width:720px;">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============== WHAT THIS MEANS PRACTICALLY ==============
eyebrow("How to actually use this")
st.markdown(
    "<h2>Good for triage. Not a substitute for an audit.</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    '<p style="font-size:15px;line-height:1.7;color:var(--ink-soft);max-width:760px;">'
    "Use this tool to get a directional answer to two questions for your jurisdiction: "
    "<strong>which sectors dominate our methane profile</strong>, and "
    "<strong>which subnational units are the largest contributors</strong>. That's enough to "
    "tell you where a mitigation strategy or a deeper, verified inventory effort would have "
    "the most impact. It is deliberately not designed to set binding targets, verify "
    "compliance, or replace a jurisdiction's own regulatory inventory — for that, pair this "
    "with facility-level verification and your own reporting processes."
    "</p>",
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ============== UPDATE CADENCE ==============
eyebrow("Update cadence")
st.markdown(
    "<h2>Refreshed on a schedule, not on demand.</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    '<p style="font-size:15px;line-height:1.7;color:var(--ink-soft);max-width:760px;">'
    "Climate TRACE itself now publishes monthly. This tool's underlying dataset is refreshed "
    "on a quarterly cycle — pulling the latest Climate TRACE release, reprocessing it into the "
    "subnational tables used across this site, and redeploying automatically. The exact "
    "&ldquo;data as of&rdquo; date for the current release is shown in the footer of every page."
    "</p>",
    unsafe_allow_html=True,
)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    '<div style="text-align:center;font-family:JetBrains Mono,monospace;font-size:10px;color:var(--ink-soft);letter-spacing:0.14em;text-transform:uppercase;padding:24px 0;border-top:1px solid var(--line);">'
    'smac prototype <span style="color:var(--copper);">✦</span> climate trace data · updated quarterly <span style="color:var(--copper);">✦</span> TESTING '
    '</div>',
    unsafe_allow_html=True,
)
