"""
Data & Methods page.
An explicit, plain-language explanation of what data powers this tool, where it
comes from, what it's good for, and where it falls short. Exists so nobody reads
a number here as more certain than it actually is. Text: i18n/<lang>.json.
"""

import streamlit as st

from utils.theme import inject_theme, eyebrow, render_footer
from utils.data_loader import (
    SECTOR_ORDER, SECTOR_COLORS, load_subsector_raw,
    CT_SNAPSHOT_DATE, CT_API_VERSION,
)
from utils.i18n import t, sector_name

inject_theme()

P = 'font-size:15px;line-height:1.7;color:var(--ink-soft);max-width:760px;'


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
        # Full list, not a truncated preview — the point of this table is to let
        # someone check how Climate TRACE's taxonomy maps onto ours. Sub-sector
        # ids stay in Climate TRACE's own (English) form on purpose: they are
        # the identifiers used in its documentation.
        examples[sec] = ", ".join(sorted(grp["sub_sector"].unique()))
    return counts, examples, int(pairs["sub_sector"].nunique())


_counts, _examples, _n_subsectors = _sector_mapping()


def _link_card(url: str, title: str, sub: str) -> None:
    st.markdown(
        f'<a href="{url}" target="_blank" style="text-decoration:none;">'
        '<div class="smac-card" style="padding:16px 20px;margin-bottom:20px;max-width:760px;">'
        '<div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:14px;color:var(--ink);">'
        f'{title} →</div>'
        f'<div style="font-size:11.5px;color:var(--ink-soft);margin-top:2px;">{sub}</div>'
        '</div></a>',
        unsafe_allow_html=True,
    )


# ============== HERO ==============
eyebrow(t("nav.methods"))
st.markdown(f"<h1 style='margin-bottom:18px;'>{t('methods.title')}</h1>", unsafe_allow_html=True)
st.markdown(
    '<p style="font-family:Quicksand,sans-serif;font-size:19px;line-height:1.65;'
    f'color:var(--ink-soft);max-width:760px;font-weight:300;">{t("methods.intro")}</p>',
    unsafe_allow_html=True,
)

st.markdown("---")

# ============== WHERE THE DATA COMES FROM ==============
eyebrow(t("methods.source_eyebrow"))
st.markdown(f"<h2>{t('methods.source_title')}</h2>", unsafe_allow_html=True)
st.markdown(
    f'<p style="{P}">{t("methods.source_p1")}</p><p style="{P}">{t("methods.source_p2")}</p>',
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    f'<p style="{P}">{t("methods.three_intro")}</p>'
    f'<ul style="{P}">'
    f'<li>{t("methods.three_1")}</li><li>{t("methods.three_2")}</li><li>{t("methods.three_3")}</li>'
    f'</ul><p style="{P}">{t("methods.method_link_intro")}</p>',
    unsafe_allow_html=True,
)
_link_card("https://github.com/climatetracecoalition", t("methods.method_link_title"),
           t("methods.method_link_sub"))

st.markdown(
    f'<p style="font-size:13px;line-height:1.6;color:var(--ink-soft);max-width:760px;'
    f'border-left:3px solid var(--line);padding-left:14px;">'
    f'{t("methods.snapshot", date=CT_SNAPSHOT_DATE, api=CT_API_VERSION)}</p>',
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ============== SECTOR TAXONOMY MAPPING ==============
eyebrow(t("methods.tax_eyebrow"))
st.markdown(f"<h2>{t('methods.tax_title')}</h2>", unsafe_allow_html=True)
st.markdown(
    f'<p style="{P}">{t("methods.tax_p1", n=_n_subsectors, k=len(SECTOR_ORDER))}</p>'
    f'<p style="{P}">{t("methods.tax_p2")}</p>',
    unsafe_allow_html=True,
)
_link_card("https://climatetrace.org/sectors", t("methods.tax_link_title"), t("methods.tax_link_sub"))

_TH = ('padding:8px 14px;border-bottom:1px solid var(--line);font-family:Quicksand,sans-serif;'
       'font-size:10px;letter-spacing:0.08em;text-transform:uppercase;color:var(--ink-soft);')
_map_rows = "".join(
    f'<tr>'
    f'<td style="padding:10px 14px;border-bottom:1px solid var(--line-soft);vertical-align:top;">'
    f'<span style="display:inline-block;width:9px;height:9px;border-radius:50%;'
    f'background:{SECTOR_COLORS.get(sec, "#b9c4bd")};margin-right:8px;"></span>'
    f'<strong>{sector_name(sec)}</strong></td>'
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
    f'<th style="text-align:left;{_TH}">{t("methods.col_ours")}</th>'
    f'<th style="text-align:left;{_TH}">{t("methods.col_ct")}</th>'
    f'<th style="text-align:right;{_TH}">{t("methods.col_count")}</th>'
    f'</tr></thead><tbody>{_map_rows}</tbody></table>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p style="font-size:12px;line-height:1.6;color:var(--ink-soft);max-width:760px;margin-top:12px;">'
    f'{t("methods.coal_note")}</p>',
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ============== LIMITATIONS ==============
eyebrow(t("methods.lim_eyebrow"))
st.markdown(f"<h2>{t('methods.lim_title')}</h2>", unsafe_allow_html=True)

for i in range(1, 7):
    st.markdown(
        f"""
        <div style="border-left:3px solid var(--copper);padding:4px 20px;margin-bottom:20px;">
          <div style="font-family:Quicksand,sans-serif;font-size:19px;font-weight:400;margin-bottom:6px;">{t(f"methods.lim{i}_title")}</div>
          <div style="font-size:14px;line-height:1.65;color:var(--ink-soft);max-width:720px;">{t(f"methods.lim{i}_desc")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============== WHAT THIS MEANS PRACTICALLY ==============
eyebrow(t("methods.use_eyebrow"))
st.markdown(f"<h2>{t('methods.use_title')}</h2>", unsafe_allow_html=True)
st.markdown(
    f'<p style="{P}">{t("methods.use_p1")}</p><p style="{P}">{t("methods.use_p2")}</p>'
    f'<p style="{P}">{t("methods.use_p3")}</p>',
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    '<p style="font-size:14px;line-height:1.7;color:var(--ink-soft);max-width:760px;'
    f'border-left:3px solid var(--mint);padding-left:14px;">{t("methods.wrong")}</p>',
    unsafe_allow_html=True,
)
if st.button(t("common.go_contact"), key="dm_contact"):
    st.switch_page("pages/6_Contact.py")

render_footer()
