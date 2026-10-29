"""
Contact & Join page.
Replicates smacmethane.org/contact — membership + research team contacts.
"""

import streamlit as st

from utils.theme import inject_theme, eyebrow, render_footer
from utils.i18n import t

inject_theme()

eyebrow(t("contact.eyebrow"))
st.markdown(f"<h1>{t('contact.title')}</h1>", unsafe_allow_html=True)
st.markdown(
    '<p style="font-family:Inter,sans-serif;font-size:16px;line-height:1.6;'
    f'color:var(--ink-soft);max-width:640px;margin-bottom:8px;">{t("contact.intro")}</p>',
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)


def contact_card(name: str, role: str, email: str, url: str | None = None):
    name_html = f'<a href="{url}" target="_blank" style="color:var(--ink);text-decoration:none;border-bottom:1px solid var(--mint);">{name}</a>' if url else name
    st.markdown(
        f"""
        <div class="smac-card" style="padding:20px 22px;margin-bottom:14px;">
          <div style="font-family:Quicksand,sans-serif;font-size:17px;font-weight:700;margin-bottom:4px;">{name_html}</div>
          <div style="font-size:13px;color:var(--ink-soft);margin-bottom:8px;line-height:1.4;">{role}</div>
          <a href="mailto:{email}" style="font-family:Quicksand,sans-serif;font-size:13px;color:var(--mint-deep);font-weight:700;text-decoration:none;">✉ {email}</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============== MEMBERSHIP ==============
eyebrow(t("contact.membership"))
st.markdown(f"<h3>{t('contact.join_h3')}</h3>", unsafe_allow_html=True)
contact_card(
    t("contact.calepa"),
    t("contact.calepa_role"),
    "methane@calepa.ca.gov",
)

st.markdown("<br>", unsafe_allow_html=True)

# ============== IMPLEMENTATION ==============
eyebrow(t("contact.implementation"))
st.markdown("<h3>Climate Group</h3>", unsafe_allow_html=True)
contact_card(
    "Jebi Rahman",
    t("contact.role_jebi"),
    "jrahman@theclimategroup.org",
)

st.markdown("<br>", unsafe_allow_html=True)

# ============== RESEARCH ==============
eyebrow(t("contact.research"))
st.markdown("<h3>Project Climate, UC Berkeley Law (CLEE)</h3>", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")
with col1:
    contact_card(
        "Ken Alex", t("contact.role_ken"),
        "ken.alex@berkeley.edu",
        "https://www.law.berkeley.edu/research/clee/about/people/ken-alex/",
    )
    contact_card(
        "Shivani Shukla", t("contact.role_shivani"),
        "shivani.shukla@berkeley.edu",
        "https://www.law.berkeley.edu/research/clee/about/people/shivani-shukla/",
    )
with col2:
    contact_card(
        "Linnan Cao", t("contact.role_fellow"),
        "lncao@berkeley.edu",
        "https://www.law.berkeley.edu/research/clee/about/people/linnan-cao/",
    )
    contact_card(
        "Max Mingxuan Xu", t("contact.role_fellow"),
        "max_xu@berkeley.edu",
    )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    f'<div class="smac-meta">{t("contact.clee")}</div>',
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ============== DATA CORRECTIONS ==============
_P = 'font-size:15px;line-height:1.7;color:var(--ink-soft);max-width:760px;'
eyebrow(t("contact.corrections"))
st.markdown(f"<h3>{t('contact.corr_h3')}</h3>", unsafe_allow_html=True)
st.markdown(
    f'<p style="{_P}">{t("contact.corr_p1")}</p><p style="{_P}">{t("contact.corr_p2")}</p>'
    f'<ul style="{_P}"><li>{t("contact.corr_li1")}</li><li>{t("contact.corr_li2")}</li></ul>',
    unsafe_allow_html=True,
)
contact_card(
    "Max Mingxuan Xu",
    t("contact.corr_role"),
    "max_xu@berkeley.edu",
)
st.markdown(
    '<div class="smac-meta" style="font-size:11.5px;max-width:760px;line-height:1.6;">'
    f'{t("contact.corr_note")}</div>',
    unsafe_allow_html=True,
)


render_footer()
