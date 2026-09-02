"""
Shared theme. Injects custom CSS to give Streamlit pages the SMAC editorial look.
Call inject_theme() at the top of every page.

v2 - production polish:
  - full mobile responsiveness (columns stack, fonts scale, padding shrinks < 760px)
  - refined hover / focus-visible states (keyboard accessibility)
  - custom scrollbar, smoother transitions
  - .typing-dots animation reserved for when chat is wired to a real LLM
  - optional component helpers (pill / spacer / thinking) to cut inline-HTML repetition
All original class names (smac-eyebrow, smac-meta, smac-struct-label,
smac-method-block, smac-flag) are preserved, so existing pages keep working untouched.
"""

import streamlit as st


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  --paper: #ffffff;
  --paper-2: #f4f8f6;
  --paper-3: #e7f5ee;
  --ink: #12161a;
  --ink-soft: #566058;
  --line: #e2e9e5;
  --line-soft: #eef3f0;
  --moss: #0e9d6c;
  --copper: #17b57e;
  --rust: #0c7a55;
  --good: #0e9d6c;
  --mint: #5ee6a8;
  --mint-deep: #0e9d6c;
  --warn: #e2574c;
  --dark: #0b0f0d;
  --shadow: 0 1px 2px rgba(11,15,13,0.04), 0 6px 20px rgba(11,15,13,0.06);
}

/* base */
html, body, [class*="css"], .stApp {
  font-family: 'Inter', sans-serif !important;
  background-color: var(--paper) !important;
  color: var(--ink) !important;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

.stApp {
  background-image:
    radial-gradient(1200px 800px at 80% -10%, rgba(23,181,126,0.06), transparent 60%),
    radial-gradient(900px 700px at -10% 90%, rgba(14,157,108,0.05), transparent 55%);
  background-attachment: fixed;
}

/* main container - widen a bit */
.main .block-container {
  padding-top: 2rem;
  padding-bottom: 4rem;
  max-width: 1280px;
}

/* sidebar */
[data-testid="stSidebar"] {
  background-color: var(--paper-2) !important;
  border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] .stMarkdown {
  font-family: 'Inter', sans-serif;
}

/* headings - bold rounded display font, matches smacmethane.org */
h1, h2, h3, h4 {
  font-family: 'Quicksand', sans-serif !important;
  font-weight: 700 !important;
  letter-spacing: -0.01em;
  color: var(--ink) !important;
}
h1 { font-size: 3rem !important; line-height: 1.05 !important; }
h2 { font-size: 2rem !important; }
h3 { font-size: 1.3rem !important; font-weight: 600 !important; }

em, i { color: var(--mint-deep); font-style: normal; font-weight: 700; }

/* dividers */
hr { border-color: var(--line-soft) !important; }

/* buttons - bright mint pill CTA, matches smacmethane.org */
.stButton > button {
  font-family: 'Quicksand', sans-serif !important;
  font-size: 15px !important;
  letter-spacing: 0 !important;
  text-transform: none !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  border: none !important;
  background: var(--mint) !important;
  color: var(--ink) !important;
  border-radius: 999px !important;
  padding: 10px 22px !important;
  font-weight: 700 !important;
  transition: background 0.2s ease, transform 0.12s ease, box-shadow 0.2s ease;
}
.stButton > button:hover {
  background: var(--mint-deep) !important;
  color: #ffffff !important;
  transform: translateY(-1px);
  box-shadow: var(--shadow);
}
.stButton > button:active { transform: translateY(0); }
.stButton > button[kind="secondary"] {
  background: var(--paper) !important;
  color: var(--ink) !important;
  border: 1.5px solid var(--line) !important;
}
.stButton > button[kind="secondary"]:hover {
  background: var(--paper-3) !important;
  border-color: var(--mint) !important;
  color: var(--ink) !important;
}
.stButton > button:focus-visible {
  outline: 2px solid var(--mint-deep) !important;
  outline-offset: 2px !important;
}

/* select boxes */
.stSelectbox label, .stRadio label {
  font-family: 'Quicksand', sans-serif !important;
  font-size: 12px !important;
  letter-spacing: 0.04em !important;
  text-transform: uppercase !important;
  color: var(--mint-deep) !important;
  font-weight: 700 !important;
}
[data-baseweb="select"] > div {
  background: var(--paper) !important;
  border-color: var(--line-soft) !important;
  border-radius: 0 !important;
  transition: border-color 0.2s ease;
}
[data-baseweb="select"] > div:hover { border-color: var(--ink) !important; }

/* radios */
.stRadio > div { gap: 4px !important; }
.stRadio [data-baseweb="radio"] {
  background: var(--paper);
  border: 1px solid var(--line-soft);
  padding: 8px 14px;
  transition: border-color 0.2s ease, background 0.2s ease;
}
.stRadio [data-baseweb="radio"]:hover { border-color: var(--ink); }

/* metric cards */
[data-testid="stMetric"] {
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 18px 22px;
}
[data-testid="stMetricLabel"] {
  font-family: 'Quicksand', sans-serif !important;
  font-size: 11px !important;
  letter-spacing: 0.08em !important;
  text-transform: uppercase !important;
  color: var(--ink-soft) !important;
  font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
  font-family: 'Quicksand', sans-serif !important;
  font-weight: 700 !important;
  font-size: 2.1rem !important;
  letter-spacing: -0.01em !important;
}
[data-testid="stMetricDelta"] {
  font-family: 'Quicksand', sans-serif !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0 !important;
}

/* tabs */
.stTabs [data-baseweb="tab-list"] {
  gap: 0;
  border-bottom: 1px solid var(--line);
}
.stTabs [data-baseweb="tab"] {
  font-family: 'Quicksand', sans-serif !important;
  font-size: 14px !important;
  letter-spacing: 0 !important;
  text-transform: none !important;
  color: var(--ink-soft) !important;
  font-weight: 600 !important;
  padding: 12px 20px !important;
  border-radius: 0 !important;
  background: transparent !important;
  border-bottom: 3px solid transparent !important;
  margin-bottom: -1px !important;
}
.stTabs [aria-selected="true"] {
  color: var(--ink) !important;
  border-bottom-color: var(--mint) !important;
  font-weight: 700 !important;
}

/* tables / dataframes */
[data-testid="stDataFrame"], [data-testid="stTable"] {
  border: 1px solid var(--line);
  border-radius: 12px;
  font-family: 'Inter', sans-serif;
}
[data-testid="stDataFrame"] thead tr th {
  background: var(--paper-2) !important;
  font-family: 'Quicksand', sans-serif !important;
  font-size: 11px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
  font-weight: 700 !important;
  color: var(--ink-soft) !important;
}

/* chat messages */
[data-testid="stChatMessage"] {
  background: var(--paper-2) !important;
  border-left: 3px solid var(--mint) !important;
  border-radius: 14px !important;
  padding: 18px 22px !important;
  margin-bottom: 16px;
}
[data-testid="stChatMessage"][data-testid*="user"] {
  background: var(--dark) !important;
  color: #ffffff !important;
  border-left: none !important;
  border-right: 3px solid var(--mint) !important;
}
[data-testid="stChatMessage"][data-testid*="user"] p {
  color: #ffffff !important;
}

/* chat input */
[data-testid="stChatInput"] {
  border: 1.5px solid var(--line) !important;
  border-radius: 999px !important;
  background: var(--paper) !important;
}
[data-testid="stChatInput"]:focus-within {
  border-color: var(--mint) !important;
  box-shadow: 0 0 0 1px var(--mint);
}

/* eyebrow class for section labels */
.smac-eyebrow {
  font-family: 'Quicksand', sans-serif;
  font-size: 13px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--mint-deep);
  font-weight: 700;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.smac-eyebrow::before {
  content: "";
  width: 24px;
  height: 3px;
  border-radius: 2px;
  background: var(--mint);
}

/* meta line */
.smac-meta {
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  letter-spacing: 0.02em;
  text-transform: none;
  color: var(--ink-soft);
}

/* struct chat blocks */
.smac-struct-label {
  font-family: 'Quicksand', sans-serif;
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-weight: 700;
  color: var(--mint-deep);
  margin-bottom: 6px;
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.smac-struct-label::before {
  content: "";
  width: 14px;
  height: 2px;
  border-radius: 2px;
  background: var(--mint);
}
.smac-method-block {
  font-family: 'Inter', sans-serif;
  font-size: 12.5px;
  color: var(--ink-soft);
  background: var(--paper-2);
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px dashed var(--line);
  line-height: 1.6;
  margin-top: 6px;
}

/* greenwashing flag */
.smac-flag {
  font-family: 'Quicksand', sans-serif;
  font-size: 12px;
  font-weight: 700;
  color: var(--mint-deep);
  letter-spacing: 0.02em;
}

/* reusable card - hover lift (add class smac-card to inline-HTML cards) */
.smac-card {
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--paper);
  transition: transform 0.15s ease, box-shadow 0.2s ease;
}
.smac-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

/* pill / tag - matches the rounded mint tags on smacmethane.org */
.smac-pill {
  display: inline-block;
  font-family: 'Quicksand', sans-serif;
  font-size: 11px;
  letter-spacing: 0.02em;
  text-transform: none;
  font-weight: 700;
  color: var(--ink);
  border: none;
  border-radius: 999px;
  background: var(--mint);
  padding: 4px 14px;
}

/* "thinking" dots - reserve for when chat is wired to a real LLM */
.typing-dots { display: inline-flex; gap: 5px; align-items: center; }
.typing-dots span {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--mint-deep);
  animation: smac-blink 1.2s infinite ease-in-out both;
}
.typing-dots span:nth-child(2) { animation-delay: 0.18s; }
.typing-dots span:nth-child(3) { animation-delay: 0.36s; }
@keyframes smac-blink {
  0%, 80%, 100% { opacity: 0.25; transform: translateY(0); }
  40% { opacity: 1; transform: translateY(-3px); }
}

/* dark accent band - full-bleed, used sparingly per smacmethane.org's design.
   Targets Streamlit's auto-generated class from st.container(key="smac-dark-band").
   Uses the standard "break out of a centered max-width container" trick
   (100vw + calc(50% - 50vw) margins) instead of a fixed -100px offset — a
   fixed offset only reaches the true page edge when the viewport happens to
   match the container's max-width; on wider screens it falls short and
   leaves a visible white gap. This version reaches the edge at any width. */
.st-key-smac-dark-band {
  background: var(--dark);
  margin-top: 32px;
  margin-left: calc(50% - 50vw);
  margin-right: calc(50% - 50vw);
  width: 100vw;
  padding: 56px calc(50vw - 50% + 40px);
  border-radius: 0;
  box-sizing: border-box;
}
.st-key-smac-dark-band h1, .st-key-smac-dark-band h2,
.st-key-smac-dark-band h3, .st-key-smac-dark-band h4 { color: #ffffff !important; }
.st-key-smac-dark-band em, .st-key-smac-dark-band i { color: var(--mint) !important; }
.st-key-smac-dark-band .smac-eyebrow { color: var(--mint) !important; }
.st-key-smac-dark-band .smac-eyebrow::before { background: var(--mint) !important; }

/* custom scrollbar */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--paper-2); }
::-webkit-scrollbar-thumb { background: var(--line-soft); border: 2px solid var(--paper-2); }
::-webkit-scrollbar-thumb:hover { background: var(--ink-soft); }

/* hide streamlit chrome */
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }

/* nicer expander */
.streamlit-expanderHeader {
  font-family: 'Quicksand', sans-serif !important;
  font-size: 13px !important;
  letter-spacing: 0.02em !important;
  text-transform: none !important;
  font-weight: 700 !important;
  color: var(--ink) !important;
}

/* ============================================================
   MOBILE RESPONSIVENESS - the biggest production gap.
   Streamlit horizontal columns do NOT stack on narrow screens
   by default, so the inline-HTML grids overflow. Force stacking.
   ============================================================ */
@media (max-width: 760px) {
  .main .block-container {
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    padding-top: 1rem !important;
  }
  h1 { font-size: 2.1rem !important; }
  h2 { font-size: 1.6rem !important; }
  h3 { font-size: 1.2rem !important; }

  [data-testid="stHorizontalBlock"] {
    flex-direction: column !important;
    gap: 12px !important;
  }
  [data-testid="stHorizontalBlock"] > [data-testid="column"] {
    width: 100% !important;
    flex: 1 1 100% !important;
    min-width: 100% !important;
  }

  [style*="font-size:42px"] { font-size: 30px !important; }

  .stButton > button {
    padding: 12px 16px !important;
    font-size: 12px !important;
  }

  [data-testid="stMetric"] { padding: 14px 16px; }
  [data-testid="stMetricValue"] { font-size: 1.7rem !important; }

  .st-key-smac-dark-band {
    padding: 36px 1.2rem !important;
  }
}

@media (max-width: 460px) {
  h1 { font-size: 1.8rem !important; }
  .smac-eyebrow, .smac-meta { font-size: 10px; letter-spacing: 0.1em; }
}

/* respect reduced-motion preferences */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    transition-duration: 0.001ms !important;
  }
}
</style>
"""


def inject_theme():
    """Inject the shared CSS. Call once at the top of each page."""
    st.markdown(CSS, unsafe_allow_html=True)


def eyebrow(text: str):
    """Render a small section eyebrow label."""
    st.markdown(f'<div class="smac-eyebrow">{text}</div>', unsafe_allow_html=True)


def meta_line(text: str):
    st.markdown(f'<div class="smac-meta">{text}</div>', unsafe_allow_html=True)


# ---- optional helpers (cut inline-HTML repetition; pages work without them) ----

def pill(text: str):
    """Small rounded mint tag/pill."""
    st.markdown(f'<span class="smac-pill">{text}</span>', unsafe_allow_html=True)


def spacer(px: int = 16):
    """Vertical whitespace."""
    st.markdown(f'<div style="height:{px}px"></div>', unsafe_allow_html=True)


def dot_logo(size: int = 40):
    """Render the SMAC 3x3 dot-grid mark (matches smacmethane.org's logo)."""
    light, dark = "#5ee6a8", "#0e9d6c"
    # corner dots lighter, edge/center dots deeper green, thin connecting lines through the center
    svg = f"""
    <svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <g stroke="{dark}" stroke-width="3" opacity="0.55">
        <line x1="15" y1="15" x2="85" y2="85"/>
        <line x1="85" y1="15" x2="15" y2="85"/>
        <line x1="50" y1="15" x2="50" y2="85"/>
        <line x1="15" y1="50" x2="85" y2="50"/>
      </g>
      <circle cx="15" cy="15" r="11" fill="{light}"/>
      <circle cx="50" cy="15" r="11" fill="{dark}"/>
      <circle cx="85" cy="15" r="11" fill="{light}"/>
      <circle cx="15" cy="50" r="11" fill="{dark}"/>
      <circle cx="50" cy="50" r="11" fill="{light}"/>
      <circle cx="85" cy="50" r="11" fill="{dark}"/>
      <circle cx="15" cy="85" r="11" fill="{light}"/>
      <circle cx="50" cy="85" r="11" fill="{dark}"/>
      <circle cx="85" cy="85" r="11" fill="{light}"/>
    </svg>
    """
    st.markdown(svg, unsafe_allow_html=True)


def dark_band():
    """Return a styled container for a full-bleed dark accent band (use for one section
    per page, not the whole site — smacmethane.org itself is white-based with a black
    band reserved for a couple of sections). Usage:

        with dark_band():
            eyebrow("Methodology")
            st.markdown("<h2>...</h2>", unsafe_allow_html=True)
            ...

    Must use st.container(key=...) (not raw HTML div/close-div across separate
    st.markdown calls) because Streamlit renders every element as its own sibling
    node — an opening <div> in one st.markdown and a closing </div> in another do
    NOT actually nest the elements in between; they render as two broken, empty
    tags instead. st.container(key=...) is the supported way to get one real
    parent element that its children actually render inside of.
    """
    return st.container(key="smac-dark-band")


def thinking():
    """Animated 'thinking...' indicator - use before a real-LLM reply streams in."""
    st.markdown(
        '<div class="typing-dots"><span></span><span></span><span></span></div>',
        unsafe_allow_html=True,
    )


def render_footer():
    """Site-wide footer — call once at the bottom of every page. Short by design
    (© line + compact link row); the fuller legal text lives in expanders so it
    doesn't need its own nav page, and doesn't bloat every page by default."""
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="border-top:1px solid var(--line);padding-top:20px;">'
        '<div style="font-family:Quicksand,sans-serif;font-size:12px;color:var(--ink-soft);line-height:1.6;">'
        "© 2026 Subnational Methane Action Coalition (SMAC) · Project Climate, "
        "UC Berkeley Law (CLEE). All rights reserved."
        "</div>"
        '<div style="font-size:11px;color:var(--ink-soft);opacity:0.75;margin-top:4px;max-width:720px;">'
        "Unless otherwise indicated, original site content, interface, and analyses are "
        "© 2026 SMAC / CLEE. Third-party datasets, logos, and trademarks (including "
        "Climate TRACE data) remain the property of their respective owners."
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
    link_cols = st.columns(6)
    with link_cols[0]:
        st.page_link("pages/1_Overview.py", label="About", icon=None)
    with link_cols[5]:
        st.page_link("pages/6_Contact.py", label="Contact", icon=None)

    exp_cols = st.columns(4)
    with exp_cols[0]:
        with st.expander("Data Sources"):
            st.markdown(
                "This site incorporates methane emissions data from Climate TRACE, an "
                "independent third-party coalition, along with contextual policy "
                "information compiled by the SMAC research team. All third-party data, "
                "trademarks, and materials remain the property of their respective "
                "owners and are subject to their original terms, licenses, and "
                "attribution requirements. Inclusion of third-party data does not imply "
                "endorsement by or affiliation with the original data providers unless "
                "explicitly stated. See **Data & Methods** for provenance and known "
                "limitations."
            )
    with exp_cols[1]:
        with st.expander("AI Disclaimer"):
            st.markdown(
                "This site uses AI-assisted tools, including a chat interface, to "
                "retrieve, summarize, analyze, or generate information about methane "
                "emissions and policy. AI-generated outputs may contain errors, "
                "omissions, or outdated information and should not be treated as "
                "authoritative professional, legal, financial, or policy advice. "
                "Verify anything important — especially before using it in official "
                "reporting or decision-making — against the underlying Climate TRACE "
                "data and cited policy sources."
            )
    with exp_cols[2]:
        with st.expander("Privacy"):
            st.markdown(
                "This site may process information you submit — for example, through "
                "the Chat feature — in order to provide its features. Please don't "
                "submit confidential, sensitive, or personally identifiable "
                "information. Where third-party hosting, analytics, or AI services are "
                "used to operate this site, information may also be processed "
                "according to those providers' own privacy policies."
            )
    with exp_cols[3]:
        with st.expander("Terms of Use"):
            st.markdown(
                "The information and tools on this site are provided for "
                "informational, research, and educational purposes. While reasonable "
                "efforts are made to keep data and analysis accurate and current, no "
                "guarantee is made regarding the completeness, accuracy, reliability, "
                "or availability of the site or its outputs. Use of this site, and any "
                "reliance on its content, is at your own discretion and risk."
            )
