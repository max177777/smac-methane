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
from utils.i18n import t

inject_theme()

_partial_months = months_in_year(CURRENT_YEAR + 1)
_n_members, _n_observers = total_member_counts()

eyebrow(t("nav.faq"))
st.markdown(f"<h1>{t('faq.title')}</h1>", unsafe_allow_html=True)
st.markdown(
    '<p style="font-family:Inter,sans-serif;font-size:16px;line-height:1.6;'
    f'color:var(--ink-soft);max-width:680px;margin-bottom:24px;">{t("faq.intro")}</p>',
    unsafe_allow_html=True,
)

# (section key, [question keys]). Each question has faq.<k>.q and faq.<k>.a in
# i18n/<lang>.json; answers take the live values below as {placeholders}.
FAQ = [
    ("data", ["source", "carbon_mapper", "inventory", "differs", "partial", "updates", "official"]),
    ("pages", ["top_sources", "enteric", "gwp", "plans", "under_construction", "global"]),
    ("smac", ["member_observer", "chat_ai", "languages", "send_data"]),
]
_vals = dict(date=CT_SNAPSHOT_DATE, api=CT_API_VERSION, range=DATA_RANGE_LABEL,
             y=CURRENT_YEAR, ny=CURRENT_YEAR + 1, n=_partial_months,
             gwp100=GWP100, gwp20=GWP20, members=_n_members, observers=_n_observers)

for section, keys in FAQ:
    eyebrow(t(f"faq.section.{section}"))
    for k in keys:
        with st.expander(t(f"faq.{k}.q", **_vals)):
            st.markdown(t(f"faq.{k}.a", **_vals))
    st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    f'<div class="smac-meta">{t("faq.not_found")}</div>',
    unsafe_allow_html=True,
)
c1, c2, _ = st.columns([1, 1, 3])
with c1:
    if st.button(t("overview.cta_methods"), key="faq_dm", use_container_width=True):
        st.switch_page("pages/5_Data_Methods.py")
with c2:
    if st.button(t("nav.contact") + " →", key="faq_contact", use_container_width=True):
        st.switch_page("pages/6_Contact.py")

render_footer()
