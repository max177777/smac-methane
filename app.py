"""
SMAC — Subnational Methane & Chat
Main entry point. Uses st.navigation for proper multi-page routing.

Run with:
    streamlit run app.py
"""

import streamlit as st


st.set_page_config(
    page_title="SMAC · Subnational Methane Insights & Chat",
    page_icon="🌫",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        "About": "The Subnational Methane Action Coalition (SMAC) is an initiative launched at COP28 that collaborates with the Center for Law, Energy & the Environment (CLEE) at UC Berkeley to help sub-national governments reduce methane emissions. CLEE serves as a key partner providing policy guidance and expertise to support SMAC’s goals in inventory development, target setting, and policy implementation. Climate TRACE data 2021–2026.",
    },
)

from utils.i18n import t, language_switcher  # noqa: E402

# Language picker, top-right of every page (see utils/i18n.py). Page titles in
# the nav bar follow the chosen language; URLs (/Country_Profile etc.) don't change.
language_switcher()

overview = st.Page("pages/1_Overview.py", title=t("nav.overview"), default=True)
data_methods = st.Page("pages/5_Data_Methods.py", title=t("nav.methods"))
country_profile = st.Page("pages/2_Country_Profile.py", title=t("nav.smac"))
global_view = st.Page("pages/8_Global_View.py", title=t("nav.global"))
comparison = st.Page("pages/3_Comparison.py", title=t("nav.compare"))
chat = st.Page("pages/4_Chat.py", title=t("nav.chat"))
faq = st.Page("pages/7_FAQ.py", title=t("nav.faq"))
contact = st.Page("pages/6_Contact.py", title=t("nav.contact"))

pg = st.navigation([overview, data_methods, country_profile, global_view, comparison, chat, faq, contact], position="top")
pg.run()
