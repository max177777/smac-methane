"""
FAQ page.
Short, plain answers to the questions members actually ask (Jalisco asked
first about Carbon Mapper). Every answer here must stay true to what the code
and data actually do — when a pipeline changes, update the matching answer.
"""

import streamlit as st

from utils.theme import inject_theme, eyebrow, render_footer
from utils.data_loader import (
    CT_SNAPSHOT_DATE, CT_API_VERSION, CURRENT_YEAR, DATA_RANGE_LABEL,
    months_in_year, total_member_counts,
)
from utils.policy_content import GWP100, GWP20

inject_theme()

_partial_months = months_in_year(CURRENT_YEAR + 1)
_n_members, _n_observers = total_member_counts()

eyebrow("FAQ")
st.markdown("<h1>Frequently asked <em>questions</em>.</h1>", unsafe_allow_html=True)
st.markdown(
    '<p style="font-family:Inter,sans-serif;font-size:16px;line-height:1.6;'
    'color:var(--ink-soft);max-width:680px;margin-bottom:24px;">'
    "Quick answers to what SMAC members ask most. For the full picture, see "
    "<strong>Data &amp; Methods</strong>; for anything not covered here, see "
    "<strong>Contact</strong>."
    "</p>",
    unsafe_allow_html=True,
)

FAQ: list[tuple[str, list[tuple[str, str]]]] = [
    ("About the data", [
        ("Where do the numbers come from?",
         f"Every emissions figure comes from **Climate TRACE**, an independent nonprofit "
         f"coalition that models emissions from satellite and remote-sensing signals, "
         f"facility-level asset data, and statistical models. This site serves the snapshot "
         f"pulled on **{CT_SNAPSHOT_DATE}** (API {CT_API_VERSION}), covering "
         f"**{DATA_RANGE_LABEL}** at monthly resolution."),
        ("Is Carbon Mapper data included?",
         "**No.** No Carbon Mapper measurements feed any figure on this site — the "
         "inventory, rankings and facility tables are all Climate TRACE.\n\n"
         "The two answer different questions. Carbon Mapper detects and quantifies "
         "individual methane **plumes** from aircraft and satellite overpasses — a "
         "snapshot of a specific leak at a specific moment. Climate TRACE estimates "
         "**total emissions over time** for every sector, including diffuse sources "
         "like agriculture that rarely produce a detectable plume. Plume observations "
         "are a powerful way to find and verify super-emitters, but they can't be added "
         "up into an annual inventory on their own.\n\n"
         "To see plume detections for your jurisdiction, use Carbon Mapper's public "
         "portal at [data.carbonmapper.org](https://data.carbonmapper.org/)."),
        ("Why doesn't a figure match our official inventory?",
         "Usually because the two are built differently. An official inventory is "
         "typically **bottom-up** — activity data and emission factors compiled by the "
         "government, often with local detail Climate TRACE doesn't have. Climate TRACE "
         "is **modeled** from remote signals and global asset data, and it allocates "
         "national totals down to subnational boundaries. Sector definitions, global "
         "warming potentials and reporting years can also differ.\n\n"
         "Where a jurisdiction publishes its own inventory, that is usually the more "
         "authoritative figure. We've integrated Maryland's state inventory alongside "
         "Climate TRACE in the Chat, and we'd like to do the same for others — send yours "
         "via **Contact**."),
        ("Why does a figure differ from climatetrace.org today?",
         "Climate TRACE revises historical estimates between releases as its models "
         f"improve. This site is pinned to the {CT_SNAPSHOT_DATE} snapshot, so a number "
         "here can legitimately differ from what climatetrace.org shows now. That's a "
         "version difference, not an error in either place."),
        (f"Why does {CURRENT_YEAR + 1} look so much lower?",
         f"Because it's a **partial year** — only {_partial_months} months are reported so "
         f"far. Wherever {CURRENT_YEAR + 1} is shown, the year-over-year change compares the "
         f"same {_partial_months} months of {CURRENT_YEAR}, not the full year, so the "
         f"comparison isn't distorted. {CURRENT_YEAR} is the latest complete year and the "
         "default everywhere."),
        ("How often is the data updated?",
         "Climate TRACE publishes a new month roughly every month, with about a 60-day "
         "lag. This site is refreshed by re-pulling the data periodically rather than "
         "live, so the snapshot date above tells you exactly which release you're seeing."),
        ("Is this an official or certified inventory?",
         "No. It's a **triage tool**: a fast, directional read on which sectors and "
         "facilities drive a jurisdiction's methane, to help decide where a mitigation "
         "strategy or a deeper verified inventory would have the most impact. It isn't "
         "designed for setting binding targets or verifying compliance."),
    ]),
    ("Reading the pages", [
        ("What are the \"top emitting sources\"?",
         "Individual named facilities from Climate TRACE — a specific landfill, plant or "
         "mine — ranked by methane. Oil & gas entries are often **field- or basin-level "
         "aggregates** rather than a single site. Road transport, forestry and most "
         "agriculture aren't listed, because there a \"source\" is a road segment or "
         "grid cell rather than a facility you could contact."),
        ("What does enteric fermentation \"pasture\" vs \"operation\" mean?",
         "Enteric fermentation is methane from livestock digestion — usually the largest "
         "agricultural source. Climate TRACE splits cattle into animals **on pasture** "
         "(grazing) and animals **in operations** (feedlots and dairies), plus other "
         "livestock. The split matters because the levers differ: feed additives and "
         "herd management apply very differently to confined versus grazing herds. Use "
         "the **Inside a sector** drill-down on the SMAC Members page to see it for your "
         "jurisdiction."),
        ("What's the difference between GWP100 and GWP20?",
         f"Both convert methane to CO₂-equivalent. **GWP100 (×{GWP100})** weighs warming "
         f"over 100 years and is the standard in most national inventories. **GWP20 "
         f"(×{GWP20})** weighs the first 20 years, when methane's effect is strongest — "
         "relevant for near-term targets. The site always labels which one is in use, "
         "since switching between them without saying so can make progress look better "
         "or worse than it is."),
        ("What does \"Existing Action Plans\" show?",
         "Plans and strategies a jurisdiction or its agencies have **already published** "
         "— SMAC doesn't author them. Where none is on file, the section is labelled "
         "**Suggested Starting Actions** instead and lists general best-practice measures "
         "for the jurisdiction's largest sectors, which are a starting point, not a plan."),
        ("Why is a jurisdiction shown as \"under construction\"?",
         "Some jurisdictions maintain a more detailed official inventory that doesn't yet "
         "line up with Climate TRACE. Rather than publish one source as if it were "
         "settled, we hold the profile back until the two are reconciled. A newly joined "
         "member can also briefly show a \"data being added\" notice until its figures "
         "are merged in."),
    ]),
    ("SMAC and this tool", [
        ("What's the difference between a member and an observer?",
         f"**Members** ({_n_members}) have formally joined the coalition and committed to "
         f"its methane goals. **Observers** ({_n_observers}) take part in SMAC convenings "
         "and use its resources but haven't made that formal commitment, often because a "
         "domestic process is still underway."),
        ("Does the Chat use AI? Can it make things up?",
         "When an AI model is connected, it writes the answer — but it's given the "
         "computed Climate TRACE figures and passages retrieved from SMAC's document "
         "library, told to use only those for any number, name or policy, and to say "
         "when it's drawing on general knowledge. Sources are listed under each answer. "
         "Check anything important against them before using it officially, and please "
         "don't enter confidential information."),
        ("Can we send our own data or a correction?",
         "Yes, please. Tell us the jurisdiction, year, sector and what you believe the "
         "right figure is — or send your official inventory and we'll work on integrating "
         "it. Details are on the **Contact** page."),
    ]),
]

for section, items in FAQ:
    eyebrow(section)
    for q, a in items:
        with st.expander(q):
            st.markdown(a)
    st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    '<div class="smac-meta">Didn\'t find your question?</div>',
    unsafe_allow_html=True,
)
c1, c2, _ = st.columns([1, 1, 3])
with c1:
    if st.button("Data & Methods →", key="faq_dm", use_container_width=True):
        st.switch_page("pages/5_Data_Methods.py")
with c2:
    if st.button("Contact →", key="faq_contact", use_container_width=True):
        st.switch_page("pages/6_Contact.py")

render_footer()
