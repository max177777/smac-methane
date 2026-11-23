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

import base64
from functools import lru_cache
from itertools import count
from pathlib import Path

import streamlit as st

# UC Berkeley Law · CLEE brand colours (sampled from CLEE's official logo files).
CLEE_GREEN = "#00553a"
CLEE_GOLD = "#f9ad0c"
CLEE_URL = "https://www.law.berkeley.edu/research/clee/"
ASSETS = Path(__file__).parent.parent / "assets"


@lru_cache(maxsize=None)
def _img_uri(name: str) -> str:
    """assets/<name> as a data: URI, so st.markdown can show it inline."""
    try:
        return "data:image/png;base64," + base64.b64encode((ASSETS / name).read_bytes()).decode()
    except OSError:
        return ""


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@500;600;700&family=Inter:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&family=Noto+Sans+KR:wght@400;500;700&family=Noto+Sans+Devanagari:wght@400;500;700&display=swap');

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
  font-family: 'Inter', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif !important;
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
/* the full-width CLEE footer is the last element: no gap under it */
[data-testid="stMainBlockContainer"], .main .block-container { padding-bottom: 0 !important; }
[data-testid="stMain"] { overflow-x: hidden; }
/* full-width footer on phones: normal side padding, left-aligned copyright */
@media (max-width: 760px) {
  .clee-site-footer .clee-ft-inner { padding: 0 1.25rem !important; }
  .clee-site-footer .clee-ft-copy { text-align: left !important; }
}
/* UC Berkeley · CLEE logo in the header, left of the page navigation */
[data-testid="stHeaderLogo"], [data-testid="stLogo"] { height: 2.6rem !important; max-width: 22rem; }

/* sidebar */
[data-testid="stSidebar"] {
  background-color: var(--paper-2) !important;
  border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] .stMarkdown {
  font-family: 'Inter', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif;
}

/* headings - bold rounded display font, matches smacmethane.org */
h1, h2, h3, h4 {
  font-family: 'Quicksand', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif !important;
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
  font-family: 'Quicksand', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif !important;
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
  font-family: 'Quicksand', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif !important;
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
  font-family: 'Quicksand', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif !important;
  font-size: 11px !important;
  letter-spacing: 0.08em !important;
  text-transform: uppercase !important;
  color: var(--ink-soft) !important;
  font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
  font-family: 'Quicksand', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif !important;
  font-weight: 700 !important;
  font-size: 2.1rem !important;
  letter-spacing: -0.01em !important;
}
[data-testid="stMetricDelta"] {
  font-family: 'Quicksand', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif !important;
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
  font-family: 'Quicksand', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif !important;
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
  font-family: 'Inter', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif;
}
[data-testid="stDataFrame"] thead tr th {
  background: var(--paper-2) !important;
  font-family: 'Quicksand', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif !important;
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
  font-family: 'Quicksand', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif;
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
  font-family: 'Inter', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif;
  font-size: 12px;
  letter-spacing: 0.02em;
  text-transform: none;
  color: var(--ink-soft);
}

/* struct chat blocks */
.smac-struct-label {
  font-family: 'Quicksand', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif;
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
  font-family: 'Inter', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif;
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
  font-family: 'Quicksand', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif;
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
  font-family: 'Quicksand', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif;
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
[class*="st-key-smac-dark-band"] {
  background: var(--dark);
  margin-top: 32px;
  margin-left: calc(50% - 50vw);
  margin-right: calc(50% - 50vw);
  width: 100vw;
  padding: 56px calc(50vw - 50% + 40px);
  border-radius: 0;
  box-sizing: border-box;
}
[class*="st-key-smac-dark-band"] h1, [class*="st-key-smac-dark-band"] h2,
[class*="st-key-smac-dark-band"] h3, [class*="st-key-smac-dark-band"] h4 { color: #ffffff !important; }
[class*="st-key-smac-dark-band"] em, [class*="st-key-smac-dark-band"] i { color: var(--mint) !important; }
[class*="st-key-smac-dark-band"] .smac-eyebrow { color: var(--mint) !important; }
[class*="st-key-smac-dark-band"] .smac-eyebrow::before { background: var(--mint) !important; }

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
  font-family: 'Quicksand', 'Noto Sans SC', 'Noto Sans KR', 'Noto Sans Devanagari', sans-serif !important;
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

  [class*="st-key-smac-dark-band"] {
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


_dark_band_counter = count()


def dark_band():
    """Return a styled container for a full-bleed dark accent band. Usage:

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

    Keys must be unique within a page, so each call gets its own suffix — the
    Overview page uses two bands ("What SMAC does" and "Methodology"), and a
    fixed key would raise a duplicate-key error on the second one. The CSS
    matches on the shared class prefix, so all of them stay styled.
    """
    return st.container(key=f"smac-dark-band-{next(_dark_band_counter)}")


def thinking():
    """Animated 'thinking...' indicator - use before a real-LLM reply streams in."""
    st.markdown(
        '<div class="typing-dots"><span></span><span></span><span></span></div>',
        unsafe_allow_html=True,
    )


def _md_bold(text: str) -> str:
    """Translation strings use **bold**; the footer is raw HTML."""
    import re
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


# Page url paths (st.navigation derives them from the file names in app.py).
FOOTER_PAGES = [("", "nav.overview"), ("Data_Methods", "nav.methods"), ("Global_View", "nav.global"),
                ("Country_Profile", "nav.smac"), ("Comparison", "nav.compare"), ("Chat", "nav.chat"),
                ("FAQ", "nav.faq"), ("Contact", "nav.contact")]


# Footer palettes, taken from the site's own colours (see :root above).
#   "light": paper-mint band, moss headings, Berkeley-blue logos — blends with the pages
#   "dark":  near-black green band, mint headings, white logos — a clear end to the page
FOOTER_STYLE = "dark"
FOOTER_THEMES = {
    "light": dict(band="#f4f8f6", border="#e2e9e5", text="#12161a", soft="#566058", head="#0e9d6c",
                  strip="#e7f5ee", strip_text="#566058", logo="clee_vertical_blue.png",
                  wordmark="uc_berkeley_wordmark_blue.png"),
    "dark": dict(band="#0f1d17", border="#0f1d17", text="#ffffff", soft="rgba(255,255,255,0.72)", head="#5ee6a8",
                 strip="#0b0f0d", strip_text="rgba(255,255,255,0.7)", logo="clee_vertical_white.png",
                 wordmark="uc_berkeley_wordmark_white.png"),
}


def render_footer():
    """Site-wide footer, full browser width like law.berkeley.edu/clee: a
    CLEE-green band (logo + who we are · page links · resources · legal notes)
    over a gold strip (UC Berkeley wordmark · copyright). Call once at the
    bottom of every page."""
    from utils.i18n import t, current_lang
    lang = current_lang()
    q = f"?lang={lang}"
    P = FOOTER_THEMES[FOOTER_STYLE]
    a = f"color:{P['text']};text-decoration:none;"
    head = (f"font-family:Quicksand,sans-serif;font-weight:700;font-size:13px;letter-spacing:0.08em;"
            f"text-transform:uppercase;color:{P['head']};"
            "margin:0 0 12px 0;")
    li = "margin:0 0 8px 0;font-size:13.5px;font-weight:600;"

    pages = "".join(f'<div style="{li}"><a href="./{path}{q}" target="_self" style="{a}">{t(key)}</a></div>'
                    for path, key in FOOTER_PAGES)
    resources = "".join(f'<div style="{li}"><a href="{url}" target="_blank" rel="noopener" style="{a}">{label} ↗</a></div>'
                        for url, label in [(CLEE_URL, "CLEE · UC Berkeley Law"),
                                           ("https://www.smacmethane.org/", "SMAC"),
                                           ("https://climatetrace.org/", "Climate TRACE")])
    legal = "".join(
        f'<details style="margin:0 0 8px 0;"><summary style="cursor:pointer;{li}margin:0;color:{P["text"]};">'
        f'{t(f"footer.{k}_title")}</summary>'
        f'<div style="font-size:12px;line-height:1.55;color:{P["soft"]};margin:6px 0 4px 0;">{_md_bold(t(f"footer.{k}_body"))}</div>'
        f"</details>" for k in ("sources", "ai", "privacy", "terms"))
    logo = _img_uri(P["logo"])
    wordmark = _img_uri(P["wordmark"])
    note = (f'<div style="font-size:11px;opacity:0.8;margin-top:4px;">{t("footer.translation_note")}</div>'
            if lang != "en" else "")
    col = "flex:1 1 180px;min-width:170px;"

    st.markdown(
        '<div class="clee-site-footer" style="position:relative;width:100vw;left:50%;margin-left:-50vw;'
        'margin-top:64px;font-family:Inter,sans-serif;">'
        # ---- green band
        f'<div style="background:{P["band"]};color:{P["text"]};border-top:1px solid {P["border"]};padding:48px 0 40px 0;">'
        '<div class="clee-ft-inner" style="max-width:1280px;box-sizing:border-box;margin:0 auto;padding:0 5rem;display:flex;flex-wrap:wrap;gap:36px 48px;">'
        f'<div style="flex:1.6 1 260px;min-width:240px;">'
        + (f'<a href="{CLEE_URL}" target="_blank" rel="noopener"><img src="{logo}" alt="UC Berkeley Center for Law, '
           f'Energy &amp; the Environment" style="height:52px;width:auto;display:block;margin-bottom:16px;"></a>'
           if logo else "")
        + f'<div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:14.5px;line-height:1.5;">{t("footer.clee_line")}</div>'
        f'<div style="font-size:12.5px;line-height:1.6;color:{P["soft"]};margin-top:6px;max-width:380px;">{t("footer.clee_body")}</div>'
        "</div>"
        f'<div style="{col}"><div style="{head}">{t("footer.explore")}</div>{pages}</div>'
        f'<div style="{col}"><div style="{head}">{t("footer.resources")}</div>{resources}</div>'
        f'<div style="{col}"><div style="{head}">{t("footer.legal")}</div>{legal}</div>'
        "</div></div>"
        # ---- gold strip
        f'<div style="background:{P["strip"]};color:{P["strip_text"]};padding:16px 0;">'
        '<div class="clee-ft-inner" style="max-width:1280px;box-sizing:border-box;margin:0 auto;padding:0 5rem;display:flex;flex-wrap:wrap;align-items:center;'
        'justify-content:space-between;gap:12px 32px;">'
        + (f'<img src="{wordmark}" alt="UC Berkeley" style="height:22px;width:auto;display:block;">' if wordmark
           else '<span style="font-weight:700;">UC Berkeley</span>')
        + f'<div class="clee-ft-copy" style="flex:1 1 320px;font-size:12px;line-height:1.5;max-width:760px;text-align:right;">{t("footer.copyright")}'
        f'<div style="font-size:11px;opacity:0.8;margin-top:2px;">{t("footer.thirdparty")}</div>{note}</div>'
        "</div></div></div>",
        unsafe_allow_html=True,
    )
