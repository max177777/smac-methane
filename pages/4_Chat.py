"""
Chat page — Methane Specialist only.
Sidebar picks a SMAC jurisdiction (single A-Z list, no country-first step) +
year + sector, which act as retrieval filters for the local RAG (utils/rag.py)
and as grounding facts for the response. When an LLM key is configured, the
model writes a genuine, question-responsive answer — RAG only supplies
material, it doesn't lock the reply into a fixed template. Without a key,
falls back to deterministic scripted templates (see utils/chat_engine.py).
"""

import unicodedata

import streamlit as st

from utils.theme import inject_theme
from utils.data_loader import (
    COUNTRY_META, list_all_locations_flat,
    DATA_RANGE_LABEL, display_name, SECTOR_ORDER, under_construction_note,
)
from utils.chat_engine import MethaneContext, build_methane_response, ChatBlock
from utils.llm import has_llm
from utils.charts import (
    time_series_plotly, jurisdiction_map_plotly, sector_bar_plotly,
    sector_trend_plotly, horizontal_bar_altair, yoy_bar_altair,
)
from utils.policy_content import get_climate_trace_detail_link
from utils.i18n import t, sector_name, country_name


inject_theme()


def _fold_accents(text: str) -> str:
    """'Córdoba' -> 'Cordoba'. Used to give accented jurisdictions a plain-ASCII
    search alias, since the selectbox filters on a literal substring match."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


# ============== STATE ==============
if "chat_iso" not in st.session_state:
    st.session_state.chat_iso = "USA"
if "chat_location" not in st.session_state:
    st.session_state.chat_location = "Maryland"
if "chat_year" not in st.session_state:
    st.session_state.chat_year = "all"
if "chat_sector" not in st.session_state:
    st.session_state.chat_sector = "all"
if "messages_methane" not in st.session_state:
    st.session_state.messages_methane = [
        # Text is looked up at render time (chat.welcome), so it follows the
        # language picker instead of freezing in whatever language was active
        # when the session started.
        {"role": "assistant", "type": "welcome", "content": ""}
    ]
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# ============== ABOUT THIS DATA (INTRO) ==============
_PS = 'font-size:14px;line-height:1.7;color:var(--ink-soft);max-width:760px;'
with st.expander(t("chat.about_title"), expanded=False):
    st.markdown(
        f'<p style="{_PS}">{t("chat.about_p1")}</p><p style="{_PS}">{t("chat.about_p2")}</p>'
        f'<p style="{_PS}">{t("chat.about_p3")}</p>'
        f'<p style="font-size:13px;line-height:1.6;color:var(--ink-soft);max-width:760px;">'
        f'{t("chat.about_p4")}</p>',
        unsafe_allow_html=True,
    )
    if st.button(t("chat.open_methods"), key="open_data_methods_from_chat"):
        st.switch_page("pages/5_Data_Methods.py")


# ============== SIDEBAR ==============
def methane_sidebar():
    with st.sidebar:
        # ---- Jurisdiction (searchable, across all 36 SMAC members) ----
        # st.selectbox is type-to-filter by default, but with 36 options that
        # affordance isn't obvious — the placeholder makes it discoverable so
        # people type "Mary" instead of scrolling. filter_mode="contains" is
        # used over the default fuzzy matching because for place names a plain
        # substring match is more predictable ("cor" -> Córdoba, not a
        # scattered subsequence hit).
        st.markdown(f'<div class="smac-eyebrow">{t("chat.sb_member")}</div>', unsafe_allow_html=True)
        flat = list_all_locations_flat()
        key_options = flat["key"].tolist()
        # 9 of the 36 jurisdictions have accented names (Córdoba, Goiás,
        # Québec, ...). Streamlit's filter is a literal substring match, so a
        # user typing "cor" on an ordinary keyboard would never find Córdoba.
        # Append an ASCII alias to those labels only, so both spellings match.
        def _search_label(row):
            base = f'{row["location"]}  ·  {country_name(row["iso3_country"])}'
            folded = _fold_accents(row["location"])
            return base if folded == row["location"] else f"{base}  ({folded})"

        label_map = {r["key"]: _search_label(r) for _, r in flat.iterrows()}
        current_key = f"{st.session_state.chat_location}||{st.session_state.chat_iso}"
        picked_key = st.selectbox(
            "jurisdiction_select",
            options=key_options,
            index=key_options.index(current_key) if current_key in key_options else 0,
            format_func=lambda k: label_map[k],
            label_visibility="collapsed",
            key="sb_jurisdiction",
            placeholder=t("chat.sb_search"),
            filter_mode="contains",
            help=t("chat.sb_search_help", n=len(key_options)),
        )
        row = flat[flat["key"] == picked_key].iloc[0]
        if row["location"] != st.session_state.chat_location or row["iso3_country"] != st.session_state.chat_iso:
            st.session_state.chat_iso = row["iso3_country"]
            st.session_state.chat_location = row["location"]
            st.rerun()

        iso = st.session_state.chat_iso
        loc = st.session_state.chat_location
        loc_display = display_name(loc)

        # ---- Satellite data ----
        # The Climate TRACE detail-page iframe is too tall for the sidebar, so
        # here we show our own compact overview map of all 36 SMAC
        # jurisdictions instead, with a link out to the selected one's own
        # detail page for the actual satellite imagery.
        st.markdown(f'<div class="smac-eyebrow">{t("chat.sb_satellite")}</div>', unsafe_allow_html=True)
        st.plotly_chart(
            jurisdiction_map_plotly(height=170, show_legend=False),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        ct_detail_link = get_climate_trace_detail_link(iso, loc)
        if ct_detail_link:
            st.markdown(
                f'<a href="{ct_detail_link}" target="_blank" style="text-decoration:none;">'
                f'<div class="smac-pill" style="display:block;text-align:center;margin:8px 0 18px;cursor:pointer;">'
                f'🛰️ {t("chat.sb_ct_detail", loc=loc_display)} →</div></a>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<a href="https://climatetrace.org/air-pollution" target="_blank" style="text-decoration:none;">'
                f'<div class="smac-pill" style="display:block;text-align:center;margin:8px 0 18px;cursor:pointer;">'
                f'🛰️ {t("chat.sb_ct_explore")} →</div></a>',
                unsafe_allow_html=True,
            )

        # ---- Question Scope (CLEAR-aligned: locks Context/Time/Evidence before answering) ----
        st.markdown(f'<div class="smac-eyebrow">{t("chat.sb_scope")}</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="smac-meta" style="font-size:9px;margin:-10px 0 12px;line-height:1.5;">'
            f'{t("chat.sb_scope_note")}</div>',
            unsafe_allow_html=True,
        )

        year_options = ["all"] + [str(y) for y in range(2026, 2020, -1)]
        year = st.selectbox(
            t("common.year"), options=year_options,
            format_func=lambda x: t("chat.all_years") if x == "all" else x,
            index=year_options.index(st.session_state.chat_year),
            key="sb_year",
        )
        if year != st.session_state.chat_year:
            st.session_state.chat_year = year
            st.rerun()

        sector_options = ["all"] + SECTOR_ORDER
        sector = st.selectbox(
            t("common.sector"), options=sector_options,
            format_func=lambda x: t("chat.all_sectors") if x == "all" else sector_name(x),
            index=sector_options.index(st.session_state.chat_sector),
            key="sb_sector",
        )
        if sector != st.session_state.chat_sector:
            st.session_state.chat_sector = sector
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(t("chat.reset"), use_container_width=True):
            st.session_state.messages_methane = st.session_state.messages_methane[:1]  # keep welcome
            st.rerun()


methane_sidebar()


# ============== UNDER-CONSTRUCTION NOTICE ==============
# The Explorer page withholds these jurisdictions entirely; the chat still
# answers (the underlying Climate TRACE numbers are real) but says up front
# that a fuller official inventory isn't reconciled in yet, so nobody reads a
# single-source figure as the settled answer.
_uc_note = under_construction_note(st.session_state.chat_iso, st.session_state.chat_location)
if _uc_note:
    from utils.i18n import tk
    st.warning(
        tk(f"uc.{st.session_state.chat_iso}.{st.session_state.chat_location}", _uc_note)
        + "\n\n" + t("chat.uc_warning"),
        icon="🚧",
    )

# ============== CONTEXT BAR ==============
iso = st.session_state.chat_iso
loc = st.session_state.chat_location
loc_display = display_name(loc)
year_label = t("chat.all_years_short") if st.session_state.chat_year == "all" else st.session_state.chat_year
sector_label = (t("chat.all_sectors") if st.session_state.chat_sector == "all"
                else sector_name(st.session_state.chat_sector))

llm_status = t("chat.status_ai") if has_llm() else t("chat.status_scripted")

st.markdown(
    f"""
    <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 0;margin-bottom:8px;flex-wrap:wrap;gap:6px;">
      <div class="smac-meta" style="font-size:11px;">
        {t("chat.context")}: <strong style="color:var(--ink);">{loc_display}</strong>
        <span style="color:var(--copper);margin:0 8px;">/</span>
        <strong style="color:var(--ink);">{country_name(iso)}</strong>
        <span style="color:var(--copper);margin:0 8px;">/</span>
        <strong style="color:var(--ink);">{year_label}</strong>
        <span style="color:var(--copper);margin:0 8px;">/</span>
        <strong style="color:var(--ink);">{sector_label}</strong>
      </div>
      <div class="smac-meta" style="font-size:10px;">
        <span style="display:inline-block;width:6px;height:6px;background:var(--good);border-radius:50%;margin-right:6px;"></span>
        {t("chat.specialist")} · {llm_status}
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
            st.markdown(t("chat.welcome"))
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

        # inline charts — picked to match the question (see _select_charts in chat_engine)
        charts = msg.get("charts")
        if charts:
            for i, ch in enumerate(charts):
                st.markdown(
                    f'<div class="smac-meta" style="margin-top:14px;font-size:10px;">'
                    f'{ch.caption}</div>',
                    unsafe_allow_html=True,
                )
                ckey = f"chart_{msg.get('id')}_{i}"
                if ch.kind == "timeseries":
                    st.plotly_chart(time_series_plotly(ch.data, height=220),
                                    use_container_width=True,
                                    config={"displayModeBar": False}, key=ckey)
                elif ch.kind == "sector_bar":
                    st.plotly_chart(sector_bar_plotly(ch.data, height=260),
                                    use_container_width=True,
                                    config={"displayModeBar": False}, key=ckey)
                elif ch.kind == "ranking_bar":
                    st.altair_chart(
                        horizontal_bar_altair(ch.data, "location", "ch4_tonnes_year",
                                              value_label="CH₄ (t)", height=260),
                        use_container_width=True, key=ckey)
                elif ch.kind == "yoy_bar":
                    st.altair_chart(
                        yoy_bar_altair(ch.data, "location", "yoy_pct", height=260),
                        use_container_width=True, key=ckey)
                elif ch.kind == "sector_trend":
                    st.plotly_chart(sector_trend_plotly(ch.data, height=280),
                                    use_container_width=True,
                                    config={"displayModeBar": False}, key=ckey)

        # legacy single-chart path (messages created before multi-chart support)
        elif msg.get("chart_df") is not None:
            st.markdown(
                f'<div class="smac-meta" style="margin-top:14px;font-size:10px;">'
                f'{t("chat.cap_monthly", subject=msg["chart_subject"], range=DATA_RANGE_LABEL)}</div>',
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
    # These are examples of what can be asked, so they shouldn't smuggle in a
    # judgement. "Why is X so high?" presumes a verdict — high relative to
    # what? — that the data doesn't support and that reads badly to a
    # jurisdiction seeing its own name in the sentence.
    return [t(f"chat.chip{i}", loc=loc_display) for i in range(1, 5)]


# ============== RENDER MESSAGES ==============
for m in st.session_state.messages_methane:
    render_methane_message(m)


# ============== SUGGESTION CHIPS BUTTONS ==============
chip_list = methane_chips()
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    '<div class="smac-meta" style="font-size:10px;margin-bottom:10px;">'
    f'<span style="color:var(--copper);">✦</span>&nbsp; {t("chat.suggested")}</div>',
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
user_input = st.chat_input(t("chat.input"))

# Resolve any pending input
final_input = user_input or st.session_state.pending_question
if final_input:
    st.session_state.pending_question = None

    st.session_state.messages_methane.append({"role": "user", "content": final_input})
    ctx = MethaneContext(
        iso=st.session_state.chat_iso,
        location=st.session_state.chat_location,
        metric="ch4",
        year=st.session_state.chat_year,
        sector=st.session_state.chat_sector,
    )
    resp = build_methane_response(final_input, ctx)
    st.session_state.messages_methane.append({
        "role": "assistant",
        "type": "structured",
        "blocks": resp.blocks,
        "charts": resp.charts,
        "chart_df": resp.chart_df,
        "chart_subject": resp.chart_subject,
        "id": len(st.session_state.messages_methane),
    })

    st.rerun()
