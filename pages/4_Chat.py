"""
Chat page — Methane Specialist only.
Sidebar drives a structured, data-grounded 5-block response: pick a SMAC
jurisdiction (single A-Z list, no country-first step) + an output type. Kept
intentionally simple so these same two selections can later drive a RAG
retrieval step once more source material is added.
"""

import streamlit as st

from utils.theme import inject_theme
from utils.data_loader import (
    COUNTRY_META, list_all_locations_flat, country_yearly, fmt_mt,
    CURRENT_YEAR, DATA_RANGE_LABEL, display_name, SECTOR_ORDER,
)
from utils.chat_engine import MethaneContext, build_methane_response, ChatBlock
from utils.llm import has_llm
from utils.charts import time_series_plotly
from utils.policy_content import get_climate_trace_detail_link


inject_theme()


# ============== STATE ==============
if "chat_iso" not in st.session_state:
    st.session_state.chat_iso = "USA"
if "chat_location" not in st.session_state:
    st.session_state.chat_location = "California"
if "chat_output" not in st.session_state:
    st.session_state.chat_output = "data"
if "chat_year" not in st.session_state:
    st.session_state.chat_year = "all"
if "chat_sector" not in st.session_state:
    st.session_state.chat_sector = "all"
if "messages_methane" not in st.session_state:
    st.session_state.messages_methane = [
        {"role": "assistant",
         "type": "welcome",
         "content": (
             "I am the SMAC Methane Specialist. I use your sidebar selections "
             "(jurisdiction and output type) to generate structured, "
             "data-grounded reasoning based on Climate TRACE methane data.\n\n"
             "Use the chips below to explore common questions, or ask your own."
         )}
    ]
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# ============== ABOUT THIS DATA (INTRO) ==============
with st.expander("ℹ️  About this data — what it is, and its limits", expanded=False):
    st.markdown(
        '<p style="font-size:14px;line-height:1.7;color:var(--ink-soft);max-width:760px;">'
        "<strong>What we're trying to do:</strong> give each jurisdiction a first-pass, "
        "directional read on <strong>which sectors and which subnational units are the "
        "largest sources of methane</strong> — a clearer sense of the major emitters — so "
        "that a government can prioritise where a real action plan is worth building. This "
        "is a triage tool, not a certified inventory."
        "</p>"
        '<p style="font-size:14px;line-height:1.7;color:var(--ink-soft);max-width:760px;">'
        "<strong>Where the numbers come from:</strong> Climate TRACE, an independent "
        "nonprofit coalition that <em>models</em> emissions from satellite imagery, remote "
        "sensors, and activity data (production volumes, land use, livestock counts) — it "
        "is inference from indirect signals, not a network of continuous ground monitors."
        "</p>"
        '<p style="font-size:14px;line-height:1.7;color:var(--ink-soft);max-width:760px;">'
        "<strong>Key deficiency to keep in mind:</strong> satellite instruments pass over a "
        "given location periodically, not continuously — so a satellite-derived estimate is "
        "closer to a series of snapshots stitched together than to a real-time emissions "
        "feed. Estimates also carry wider uncertainty for diffuse sources (small-scale "
        "agriculture, informal waste) than for large point sources (oil &amp; gas "
        "facilities), and the subnational split itself is a modeled allocation, not a "
        "jurisdiction's own self-report."
        "</p>"
        '<p style="font-size:13px;line-height:1.6;color:var(--ink-soft);max-width:760px;">'
        "See the full <strong>Data &amp; Methods</strong> page for the complete picture, "
        "including known limitations."
        "</p>",
        unsafe_allow_html=True,
    )
    if st.button("Open Data & Methods →", key="open_data_methods_from_chat"):
        st.switch_page("pages/5_Data_Methods.py")


# ============== SIDEBAR ==============
def methane_sidebar():
    with st.sidebar:
        # ---- Jurisdiction (single A-Z list across all 36 SMAC members) ----
        st.markdown('<div class="smac-eyebrow">SMAC member</div>', unsafe_allow_html=True)
        flat = list_all_locations_flat()
        key_options = flat["key"].tolist()
        label_map = dict(zip(flat["key"], flat["label"]))
        current_key = f"{st.session_state.chat_location}||{st.session_state.chat_iso}"
        picked_key = st.selectbox(
            "jurisdiction_select",
            options=key_options,
            index=key_options.index(current_key) if current_key in key_options else 0,
            format_func=lambda k: label_map[k],
            label_visibility="collapsed",
            key="sb_jurisdiction",
            help="Every SMAC member/observer jurisdiction, alphabetised — this selection "
                 "(plus output type below) is what will drive retrieval once this chat is "
                 "connected to a fuller RAG knowledge base.",
        )
        row = flat[flat["key"] == picked_key].iloc[0]
        if row["location"] != st.session_state.chat_location or row["iso3_country"] != st.session_state.chat_iso:
            st.session_state.chat_iso = row["iso3_country"]
            st.session_state.chat_location = row["location"]
            st.rerun()

        iso = st.session_state.chat_iso
        loc = st.session_state.chat_location
        loc_display = display_name(loc)

        cy = country_yearly(iso)
        y_now = float(cy[cy["year"] == CURRENT_YEAR]["ch4_tonnes"].iloc[0]) if CURRENT_YEAR in cy["year"].values else 0
        st.markdown(
            f"<div class='smac-meta' style='margin:-2px 0 18px;font-size:10px;'>"
            f"part of {COUNTRY_META[iso]['name']}</div>",
            unsafe_allow_html=True,
        )

        # ---- Satellite data ----
        st.markdown('<div class="smac-eyebrow">Satellite data</div>', unsafe_allow_html=True)
        ct_detail_link = get_climate_trace_detail_link(iso, loc)
        if ct_detail_link:
            import streamlit.components.v1 as components
            components.iframe(ct_detail_link, height=220)
            st.markdown(
                f'<div class="smac-meta" style="font-size:9px;margin:6px 0 10px;line-height:1.5;">'
                f'<a href="{ct_detail_link}" target="_blank" style="color:var(--mint-deep);">'
                f'open full detail page on Climate TRACE →</a></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<a href="https://climatetrace.org/air-pollution" target="_blank" style="text-decoration:none;">'
                f'<div class="smac-pill" style="display:block;text-align:center;margin-bottom:18px;cursor:pointer;">'
                f'🛰️ Explore Climate TRACE →</div></a>',
                unsafe_allow_html=True,
            )

        # ---- Question Scope (CLEAR-aligned: locks Context/Time/Evidence before answering) ----
        st.markdown('<div class="smac-eyebrow">Question scope</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="smac-meta" style="font-size:9px;margin:-10px 0 12px;line-height:1.5;">'
            'pins the year and sector so the answer — and what it retrieves from the document '
            'library — stays locked to what you actually asked, instead of drifting to '
            'whatever\'s most recent or most generic.</div>',
            unsafe_allow_html=True,
        )

        year_options = ["all"] + [str(y) for y in range(2026, 2020, -1)]
        year = st.selectbox(
            "Year", options=year_options,
            format_func=lambda x: "All years (2021–2026)" if x == "all" else x,
            index=year_options.index(st.session_state.chat_year),
            key="sb_year",
        )
        if year != st.session_state.chat_year:
            st.session_state.chat_year = year
            st.rerun()

        sector_options = ["all"] + SECTOR_ORDER
        sector = st.selectbox(
            "Sector", options=sector_options,
            format_func=lambda x: "All sectors" if x == "all" else x,
            index=sector_options.index(st.session_state.chat_sector),
            key="sb_sector",
        )
        if sector != st.session_state.chat_sector:
            st.session_state.chat_sector = sector
            st.rerun()

        output_options = {
            "data": "Data summary",
            "trend": "Trend analysis",
            "policy": "Policy analysis",
            "pathway": "Mitigation pathway",
            "method": "Method explanation",
        }
        output = st.selectbox(
            "Output type", options=list(output_options.keys()),
            format_func=lambda x: output_options[x],
            index=list(output_options.keys()).index(st.session_state.chat_output),
            key="sb_output",
        )
        if output != st.session_state.chat_output:
            st.session_state.chat_output = output
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Reset conversation", use_container_width=True):
            st.session_state.messages_methane = st.session_state.messages_methane[:1]  # keep welcome
            st.rerun()


methane_sidebar()


# ============== CONTEXT BAR ==============
iso = st.session_state.chat_iso
loc = st.session_state.chat_location
loc_display = display_name(loc)
output_label = {"data": "Data summary", "trend": "Trend analysis", "policy": "Policy analysis",
                "pathway": "Mitigation pathway", "method": "Method explanation"}[st.session_state.chat_output]
year_label = "All years" if st.session_state.chat_year == "all" else st.session_state.chat_year
sector_label = "All sectors" if st.session_state.chat_sector == "all" else st.session_state.chat_sector

llm_status = "AI-enriched · grounded in real data" if has_llm() else "scripted · grounded in real data"

st.markdown(
    f"""
    <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 0;margin-bottom:8px;flex-wrap:wrap;gap:6px;">
      <div class="smac-meta" style="font-size:11px;">
        context: <strong style="color:var(--ink);">{loc_display}</strong>
        <span style="color:var(--copper);margin:0 8px;">/</span>
        <strong style="color:var(--ink);">{COUNTRY_META[iso]['name']}</strong>
        <span style="color:var(--copper);margin:0 8px;">/</span>
        <strong style="color:var(--ink);">{year_label}</strong>
        <span style="color:var(--copper);margin:0 8px;">/</span>
        <strong style="color:var(--ink);">{sector_label}</strong>
        <span style="color:var(--copper);margin:0 8px;">/</span>
        <strong style="color:var(--ink);">{output_label}</strong>
      </div>
      <div class="smac-meta" style="font-size:10px;">
        <span style="display:inline-block;width:6px;height:6px;background:var(--good);border-radius:50%;margin-right:6px;"></span>
        methane specialist · {llm_status}
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============== HELPERS TO RENDER MESSAGES ==============
def render_methane_message(msg: dict):
    """Render an assistant methane message (structured) or user message."""
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
        return

    with st.chat_message("assistant"):
        if msg.get("type") == "welcome":
            st.markdown(msg["content"])
            return
        # structured blocks
        for block in msg["blocks"]:
            label_html = f'<div class="smac-struct-label">{block.label}</div>'
            st.markdown(label_html, unsafe_allow_html=True)
            if block.is_method:
                st.markdown(
                    f'<div class="smac-method-block">{block.content}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(block.content)

        # inline mini chart
        if msg.get("chart_df") is not None:
            st.markdown(
                f'<div class="smac-meta" style="margin-top:14px;font-size:10px;">'
                f'{msg["chart_subject"]} · monthly CH₄ tonnes · {DATA_RANGE_LABEL}</div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                time_series_plotly(msg["chart_df"], height=220),
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"chart_{msg.get('id')}",
            )


# ============== SUGGESTED CHIPS ==============
def methane_chips():
    return [
        f"Show {loc_display}'s methane trend",
        f"Why is {loc_display} so high?",
        f"What policy fits {loc_display}?",
        f"Top emission sources in {loc_display}",
    ]


# ============== RENDER MESSAGES ==============
for m in st.session_state.messages_methane:
    render_methane_message(m)


# ============== SUGGESTION CHIPS BUTTONS ==============
chip_list = methane_chips()
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    '<div class="smac-meta" style="font-size:10px;margin-bottom:10px;">'
    '<span style="color:var(--copper);">✦</span>&nbsp; Suggested prompts</div>',
    unsafe_allow_html=True,
)
chip_cols = st.columns(len(chip_list))
for i, q in enumerate(chip_list):
    with chip_cols[i]:
        if st.button(q, key=f"chip_{i}_{hash(q)}", use_container_width=True, type="secondary"):
            st.session_state.pending_question = q
            st.rerun()


# ============== CHAT INPUT ==============
# No render_footer() on this page — it sits right above the chat input and gets in
# the way of the actual chat interaction.
user_input = st.chat_input("Ask about emissions, policy, or mitigation pathways…")

# Resolve any pending input
final_input = user_input or st.session_state.pending_question
if final_input:
    st.session_state.pending_question = None

    st.session_state.messages_methane.append({"role": "user", "content": final_input})
    ctx = MethaneContext(
        iso=st.session_state.chat_iso,
        location=st.session_state.chat_location,
        metric="ch4",
        output=st.session_state.chat_output,
        year=st.session_state.chat_year,
        sector=st.session_state.chat_sector,
    )
    resp = build_methane_response(final_input, ctx)
    st.session_state.messages_methane.append({
        "role": "assistant",
        "type": "structured",
        "blocks": resp.blocks,
        "chart_df": resp.chart_df,
        "chart_subject": resp.chart_subject,
        "id": len(st.session_state.messages_methane),
    })

    st.rerun()
