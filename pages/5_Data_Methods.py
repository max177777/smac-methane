"""
Data & Methods page.
An explicit, plain-language explanation of what data powers this tool, where it
comes from, what it's good for, and where it falls short. Exists so nobody reads
a number here as more certain than it actually is.
"""

import streamlit as st

from utils.theme import inject_theme, eyebrow, render_footer
from utils.data_loader import (
    SECTOR_ORDER, SECTOR_COLORS, load_subsector_raw,
    CT_SNAPSHOT_DATE, CT_API_VERSION,
)


inject_theme()


# Sector-mapping figures are DERIVED from the actual dataset rather than
# hand-written, so this page can't drift out of sync with the taxonomy in
# scripts/build_subsector_data.py if sub-sectors are added or regrouped.
@st.cache_data(show_spinner=False)
def _sector_mapping():
    """(counts per broad sector, example sub-sector names per broad sector,
    total distinct sub-sectors) straight from the sub-sector dataset."""
    df = load_subsector_raw()
    if df.empty:
        return {}, {}, 0
    pairs = df[["sector", "sub_sector"]].drop_duplicates()
    counts = pairs.groupby("sector")["sub_sector"].nunique().to_dict()
    examples = {}
    for sec, grp in pairs.groupby("sector"):
        names = sorted(grp["sub_sector"].unique())
        # Full list, not a truncated preview — the whole point of this table is
        # to let someone check how Climate TRACE's taxonomy maps onto ours, and
        # "+11 more" hides exactly the detail they came to look up.
        examples[sec] = ", ".join(names)
    return counts, examples, int(pairs["sub_sector"].nunique())


_counts, _examples, _n_subsectors = _sector_mapping()

# ============== HERO ==============
eyebrow("Data & Methods")
st.markdown(
    "<h1 style='margin-bottom:18px;'>What this tool is — "
    "<em>and isn't.</em></h1>",
    unsafe_allow_html=True,
)
st.markdown(
    '<p style="font-family:Quicksand,sans-serif;font-size:19px;line-height:1.65;'
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
    "state/province, and more than 740 million individual facilities and assets worldwide. It "
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

st.markdown(
    '<p style="font-size:15px;line-height:1.7;color:var(--ink-soft);max-width:760px;">'
    "<strong>Three things go into those estimates</strong>, and it's worth being precise "
    "about the mix rather than calling it all &ldquo;satellite data&rdquo;:"
    "</p>"
    '<ul style="font-size:15px;line-height:1.7;color:var(--ink-soft);max-width:760px;">'
    "<li><strong>Satellite and remote-sensing signals</strong> — direct observation of "
    "plumes, thermal signatures, land cover and activity indicators.</li>"
    "<li><strong>Global asset-level data</strong> — the locations of individual facilities, "
    "their size, their technology and operating characteristics. This is what makes a "
    "facility-by-facility ranking possible at all, rather than a national total split by "
    "population or GDP.</li>"
    "<li><strong>Machine learning and other statistical models</strong> — used to fill gaps "
    "where direct observation isn't available, and to convert observed activity into an "
    "emissions estimate.</li>"
    "</ul>"
    '<p style="font-size:15px;line-height:1.7;color:var(--ink-soft);max-width:760px;">'
    "The full sector-by-sector methodology is published openly:"
    "</p>",
    unsafe_allow_html=True,
)
st.markdown(
    '<a href="https://github.com/climatetracecoalition" target="_blank" style="text-decoration:none;">'
    '<div class="smac-card" style="padding:16px 20px;margin-bottom:20px;max-width:760px;">'
    '<div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:14px;color:var(--ink);">'
    'Climate TRACE methodology documentation \u2192</div>'
    '<div style="font-size:11.5px;color:var(--ink-soft);margin-top:2px;">'
    'github.com/climatetracecoalition — the per-sector method docs behind every '
    'estimate shown in this tool</div>'
    '</div></a>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<p style="font-size:13px;line-height:1.6;color:var(--ink-soft);max-width:760px;'
    f'border-left:3px solid var(--line);padding-left:14px;">'
    f"<strong>Which snapshot you're looking at.</strong> The figures on this site were "
    f"pulled from Climate TRACE on <strong>{CT_SNAPSHOT_DATE}</strong> (API "
    f"{CT_API_VERSION}). Climate TRACE improves its models continuously and revises "
    f"historical estimates between releases, so a figure here can legitimately differ from "
    f"climatetrace.org today, or from what this site showed a few months ago. That's a "
    f"version difference, not an error in either place."
    f"</p>",
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ============== SECTOR TAXONOMY MAPPING ==============
eyebrow("Sector taxonomy")
st.markdown(
    "<h2>How Climate TRACE's sectors map to ours.</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    '<p style="font-size:15px;line-height:1.7;color:var(--ink-soft);max-width:760px;">'
    "Climate TRACE publishes emissions under a detailed taxonomy of "
    f"<strong>{_n_subsectors} activity-level sub-sectors</strong> "
    "(<em>oil-and-gas-production</em>, <em>enteric-fermentation-cattle-pasture</em>, "
    "<em>solid-waste-disposal</em>, and so on), grouped under a set of top-level sectors. "
    "This tool rolls those up into "
    f"<strong>{len(SECTOR_ORDER)} broad categories</strong> so that a jurisdiction's "
    "profile stays readable — but the underlying sub-sector detail is preserved, and it's "
    "what drives the <strong>Top emitting sources</strong> table on the SMAC Explorer page."
    "</p>"
    '<p style="font-size:15px;line-height:1.7;color:var(--ink-soft);max-width:760px;">'
    "You can browse Climate TRACE's own sector definitions — including the methodology "
    "documentation behind each one — on their site:"
    "</p>",
    unsafe_allow_html=True,
)
st.markdown(
    '<a href="https://climatetrace.org/sectors" target="_blank" style="text-decoration:none;">'
    '<div class="smac-card" style="padding:16px 20px;margin-bottom:20px;max-width:760px;">'
    '<div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:14px;color:var(--ink);">'
    'Climate TRACE — sector taxonomy &amp; methodologies \u2192</div>'
    '<div style="font-size:11.5px;color:var(--ink-soft);margin-top:2px;">'
    'climatetrace.org/sectors — definitions, sub-sector lists, and the method docs '
    'for how each sector is estimated</div>'
    '</div></a>',
    unsafe_allow_html=True,
)

_map_rows = "".join(
    f'<tr>'
    f'<td style="padding:10px 14px;border-bottom:1px solid var(--line-soft);vertical-align:top;">'
    f'<span style="display:inline-block;width:9px;height:9px;border-radius:50%;'
    f'background:{SECTOR_COLORS.get(sec, "#b9c4bd")};margin-right:8px;"></span>'
    f'<strong>{sec}</strong></td>'
    f'<td style="padding:10px 14px;border-bottom:1px solid var(--line-soft);vertical-align:top;'
    f'font-size:12px;color:var(--ink-soft);line-height:1.6;">{_examples.get(sec, "—")}</td>'
    f'<td style="padding:10px 14px;border-bottom:1px solid var(--line-soft);vertical-align:top;'
    f'font-family:Quicksand,sans-serif;font-size:12px;color:var(--ink-soft);text-align:right;">'
    f'{_counts.get(sec, 0)}</td>'
    f'</tr>'
    for sec in SECTOR_ORDER
)
st.markdown(
    f'<table style="width:100%;max-width:900px;border-collapse:collapse;font-family:Inter,sans-serif;">'
    f'<thead><tr>'
    f'<th style="text-align:left;padding:8px 14px;border-bottom:1px solid var(--line);'
    f'font-family:Quicksand,sans-serif;font-size:10px;letter-spacing:0.08em;'
    f'text-transform:uppercase;color:var(--ink-soft);">Our category</th>'
    f'<th style="text-align:left;padding:8px 14px;border-bottom:1px solid var(--line);'
    f'font-family:Quicksand,sans-serif;font-size:10px;letter-spacing:0.08em;'
    f'text-transform:uppercase;color:var(--ink-soft);">Climate TRACE sub-sectors it absorbs</th>'
    f'<th style="text-align:right;padding:8px 14px;border-bottom:1px solid var(--line);'
    f'font-family:Quicksand,sans-serif;font-size:10px;letter-spacing:0.08em;'
    f'text-transform:uppercase;color:var(--ink-soft);">Count</th>'
    f'</tr></thead><tbody>{_map_rows}</tbody></table>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p style="font-size:12px;line-height:1.6;color:var(--ink-soft);max-width:760px;margin-top:12px;">'
    "One grouping decision worth flagging: Climate TRACE already classifies "
    "<em>coal-mining</em> under fossil fuels, so that isn't something we moved — it sits in "
    "our <strong>Fossil Fuel Extraction &amp; Mining</strong> category exactly where Climate "
    "TRACE puts it. What we did fold in is Climate TRACE's separate "
    "<em>mineral-extraction</em> sector (copper, iron, bauxite, quarrying). For methane "
    "specifically those contribute essentially nothing — together they account for under "
    "0.02% of the category, and most report zero CH₄ outright — so giving them their own "
    "top-level slot would add a visual category that is empty in every jurisdiction. If you "
    "are looking at CO₂ rather than methane, that trade-off would not hold."
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
          <div style="font-family:Quicksand,sans-serif;font-size:19px;font-weight:400;margin-bottom:6px;">{title}</div>
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
    "Use this tool to get a directional answer to three questions for your jurisdiction: "
    "<strong>which sectors dominate our methane profile</strong>, "
    "<strong>which subnational units and facilities are the largest contributors</strong>, and "
    "<strong>where the biggest opportunities for decarbonization are</strong>. That's enough to "
    "tell you where a mitigation strategy or a deeper, verified inventory effort would have "
    "the most impact."
    "</p>"
    '<p style="font-size:15px;line-height:1.7;color:var(--ink-soft);max-width:760px;">'
    "There's a second use worth knowing about. Official inventories are published in "
    "multi-year cycles, so there is usually a long gap between the last verified figure and "
    "the present. Because Climate TRACE updates continuously, it can show how emissions have "
    "moved <strong>between inventories, or while an inventory update is still underway</strong> "
    "— which means it can give an early read on whether a methane abatement action is working "
    "before the next official inventory would confirm it."
    "</p>"
    '<p style="font-size:15px;line-height:1.7;color:var(--ink-soft);max-width:760px;">'
    "It is deliberately not designed to set binding targets, verify compliance, or replace a "
    "jurisdiction's own regulatory inventory — for that, pair this with facility-level "
    "verification and your own reporting processes."
    "</p>",
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    '<p style="font-size:14px;line-height:1.7;color:var(--ink-soft);max-width:760px;'
    'border-left:3px solid var(--mint);padding-left:14px;">'
    "<strong>Think a number here is wrong?</strong> Tell us. Where a jurisdiction publishes "
    "its own inventory, that is usually the more authoritative figure, and we would rather "
    "integrate it than have this tool quietly disagree with it. See the "
    "<strong>Contact</strong> page for how to send a correction or an inventory."
    "</p>",
    unsafe_allow_html=True,
)
if st.button("Go to Contact →", key="dm_contact"):
    st.switch_page("pages/6_Contact.py")


render_footer()
