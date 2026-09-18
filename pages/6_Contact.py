"""
Contact & Join page.
Replicates smacmethane.org/contact — membership + research team contacts.
"""

import streamlit as st

from utils.theme import inject_theme, eyebrow, render_footer

inject_theme()

eyebrow("Contact & Join")
st.markdown("<h1>Get in <em>touch</em>.</h1>", unsafe_allow_html=True)
st.markdown(
    '<p style="font-family:Inter,sans-serif;font-size:16px;line-height:1.6;'
    'color:var(--ink-soft);max-width:640px;margin-bottom:8px;">'
    "Joining SMAC is always free. Reach out below to join as a member, or to "
    "connect with the research team behind this tool."
    "</p>",
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
eyebrow("Membership")
st.markdown("<h3>Want your jurisdiction to join SMAC?</h3>", unsafe_allow_html=True)
contact_card(
    "The California Environmental Protection Agency",
    "SMAC Secretariat — membership inquiries",
    "methane@calepa.ca.gov",
)

st.markdown("<br>", unsafe_allow_html=True)

# ============== IMPLEMENTATION ==============
eyebrow("Implementation")
st.markdown("<h3>Climate Group</h3>", unsafe_allow_html=True)
contact_card(
    "Jebi Rahman",
    "Director of Global Implementation, Climate Group",
    "jrahman@theclimategroup.org",
)

st.markdown("<br>", unsafe_allow_html=True)

# ============== RESEARCH ==============
eyebrow("Research")
st.markdown("<h3>Project Climate, UC Berkeley Law (CLEE)</h3>", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")
with col1:
    contact_card(
        "Ken Alex", "Director, Project Climate, UC Berkeley",
        "ken.alex@berkeley.edu",
        "https://www.law.berkeley.edu/research/clee/about/people/ken-alex/",
    )
    contact_card(
        "Shivani Shukla", "Lead Methane Research Fellow, Project Climate, UC Berkeley",
        "shivani.shukla@berkeley.edu",
        "https://www.law.berkeley.edu/research/clee/about/people/shivani-shukla/",
    )
with col2:
    contact_card(
        "Linnan Cao", "Methane Research Fellow, Project Climate, UC Berkeley",
        "lncao@berkeley.edu",
        "https://www.law.berkeley.edu/research/clee/about/people/linnan-cao/",
    )
    contact_card(
        "Max Mingxuan Xu", "Methane Research Fellow, Project Climate, UC Berkeley",
        "max_xu@berkeley.edu",
    )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    '<div class="smac-meta">Center for Law, Energy &amp; the Environment (CLEE) · '
    'UC Berkeley Law</div>',
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ============== DATA CORRECTIONS ==============
eyebrow("Data corrections")
st.markdown("<h3>See a figure that looks wrong?</h3>", unsafe_allow_html=True)
st.markdown(
    '<p style="font-size:15px;line-height:1.7;color:var(--ink-soft);max-width:760px;">'
    "Most figures in this tool are modelled estimates from Climate TRACE, not measurements "
    "and not a jurisdiction's own reported inventory. Where a government maintains its own "
    "inventory, the two can disagree — sometimes substantially — and the official inventory "
    "is usually the more authoritative of the pair for that jurisdiction."
    "</p>"
    '<p style="font-size:15px;line-height:1.7;color:var(--ink-soft);max-width:760px;">'
    "So if something here looks wrong for your jurisdiction, we would rather hear it than "
    "not. Two things are especially useful to us:"
    "</p>"
    '<ul style="font-size:15px;line-height:1.7;color:var(--ink-soft);max-width:760px;">'
    "<li><strong>A figure you believe is inaccurate</strong> — tell us which jurisdiction, "
    "year and sector, and what you think the right number is.</li>"
    "<li><strong>An official inventory we should be reading</strong> — if your jurisdiction "
    "publishes its own greenhouse gas or methane inventory, send it over. We have already "
    "integrated Maryland's state inventory this way, and we would like to do the same for "
    "others.</li>"
    "</ul>",
    unsafe_allow_html=True,
)
contact_card(
    "Max Mingxuan Xu",
    "Data corrections and inventory contributions",
    "max_xu@berkeley.edu",
)
st.markdown(
    '<div class="smac-meta" style="font-size:11.5px;max-width:760px;line-height:1.6;">'
    "Where a jurisdiction's own inventory is still being reconciled against Climate TRACE, "
    "its profile is marked <strong>under construction</strong> rather than shown with one "
    "source standing in for the other. See <strong>Data &amp; Methods</strong> for what the "
    "underlying data can and cannot support."
    "</div>",
    unsafe_allow_html=True,
)


render_footer()
