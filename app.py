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
        "About": "The Subnational Methane Action Coalition (SMAC) is an initiative launched at COP28 that collaborates with the Center for Law, Energy & the Environment (CLEE) at UC Berkeley to help sub-national governments reduce methane emissions. CLEE serves as a key partner providing policy guidance and expertise to support SMAC’s goals in inventory development, target setting, and policy implementation. Climate TRACE data 2021-2024.",
    },
)

overview = st.Page("pages/1_Overview.py", title="Overview", default=True)
data_methods = st.Page("pages/5_Data_Methods.py", title="Data & Methods")
atlas = st.Page("pages/2_Atlas.py", title="SMAC")
insights = st.Page("pages/3_Insights.py", title="Insights")
chat = st.Page("pages/4_Chat.py", title="Chat")

pg = st.navigation([overview, data_methods, atlas, insights, chat], position="top")
pg.run()
