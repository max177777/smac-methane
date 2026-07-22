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
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,500;9..144,700&family=JetBrains+Mono:wght@300;400;500;700&family=Inter+Tight:wght@300;400;500;600;700&display=swap');

:root {
  --paper: #f4efe6;
  --paper-2: #ebe4d6;
  --paper-3: #e0d7c4;
  --ink: #1a1f1a;
  --ink-soft: #3a4239;
  --line: #3a4239;
  --line-soft: #c4bca8;
  --moss: #2d4a36;
  --copper: #b5612a;
  --rust: #7a3a1a;
  --good: #4a6b3e;
  --shadow: 0 1px 2px rgba(26,31,26,0.04), 0 6px 20px rgba(26,31,26,0.05);
}

/* base */
html, body, [class*="css"], .stApp {
  font-family: 'Inter Tight', sans-serif !important;
  background-color: var(--paper) !important;
  color: var(--ink) !important;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

.stApp {
  background-image:
    radial-gradient(1200px 800px at 80% -10%, rgba(181,97,42,0.05), transparent 60%),
    radial-gradient(900px 700px at -10% 90%, rgba(45,74,54,0.08), transparent 55%);
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
  font-family: 'Inter Tight', sans-serif;
}

/* headings - serif display */
h1, h2, h3, h4 {
  font-family: 'Fraunces', serif !important;
  font-weight: 300 !important;
  letter-spacing: -0.02em;
  color: var(--ink) !important;
}
h1 { font-size: 3.2rem !important; line-height: 1 !important; }
h2 { font-size: 2.2rem !important; }
h3 { font-size: 1.4rem !important; font-weight: 400 !important; }

em, i { color: var(--moss); font-style: italic; }

/* dividers */
hr { border-color: var(--line-soft) !important; }

/* buttons */
.stButton > button {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 11px !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  border: 1.5px solid var(--ink) !important;
  background: var(--ink) !important;
  color: var(--paper) !important;
  border-radius: 0 !important;
  padding: 8px 18px !important;
  font-weight: 500 !important;
  transition: background 0.2s ease, border-color 0.2s ease, transform 0.12s ease, box-shadow 0.2s ease;
}
.stButton > button:hover {
  background: var(--moss) !important;
  border-color: var(--moss) !important;
  transform: translateY(-1px);
  box-shadow: var(--shadow);
}
.stButton > button:active { transform: translateY(0); }
.stButton > button[kind="secondary"] {
  background: transparent !important;
  color: var(--ink) !important;
}
.stButton > button[kind="secondary"]:hover {
  background: var(--ink) !important;
  color: var(--paper) !important;
}
.stButton > button:focus-visible {
  outline: 2px solid var(--copper) !important;
  outline-offset: 2px !important;
}

/* select boxes */
.stSelectbox label, .stRadio label {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 10px !important;
  letter-spacing: 0.16em !important;
  text-transform: uppercase !important;
  color: var(--copper) !important;
  font-weight: 500 !important;
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
  padding: 18px 22px;
}
[data-testid="stMetricLabel"] {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 10px !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  color: var(--ink-soft) !important;
}
[data-testid="stMetricValue"] {
  font-family: 'Fraunces', serif !important;
  font-weight: 300 !important;
  font-size: 2.2rem !important;
  letter-spacing: -0.02em !important;
}
[data-testid="stMetricDelta"] {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 11px !important;
  letter-spacing: 0.06em !important;
}

/* tabs */
.stTabs [data-baseweb="tab-list"] {
  gap: 0;
  border-bottom: 1px solid var(--line);
}
.stTabs [data-baseweb="tab"] {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 11px !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  color: var(--ink-soft) !important;
  padding: 12px 20px !important;
  border-radius: 0 !important;
  background: transparent !important;
  border-bottom: 2px solid transparent !important;
  margin-bottom: -1px !important;
}
.stTabs [aria-selected="true"] {
  color: var(--ink) !important;
  border-bottom-color: var(--copper) !important;
  font-weight: 500 !important;
}

/* tables / dataframes */
[data-testid="stDataFrame"], [data-testid="stTable"] {
  border: 1px solid var(--line);
  font-family: 'Inter Tight', sans-serif;
}
[data-testid="stDataFrame"] thead tr th {
  background: var(--paper-2) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 10px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.12em !important;
  color: var(--ink-soft) !important;
}

/* chat messages */
[data-testid="stChatMessage"] {
  background: var(--paper-2) !important;
  border-left: 3px solid var(--copper) !important;
  border-radius: 0 !important;
  padding: 18px 22px !important;
  margin-bottom: 16px;
}
[data-testid="stChatMessage"][data-testid*="user"] {
  background: var(--ink) !important;
  color: var(--paper) !important;
  border-left: none !important;
  border-right: 3px solid var(--copper) !important;
}
[data-testid="stChatMessage"][data-testid*="user"] p {
  color: var(--paper) !important;
}

/* chat input */
[data-testid="stChatInput"] {
  border: 1.5px solid var(--ink) !important;
  border-radius: 0 !important;
  background: var(--paper) !important;
}
[data-testid="stChatInput"]:focus-within {
  border-color: var(--copper) !important;
  box-shadow: 0 0 0 1px var(--copper);
}

/* eyebrow class for section labels */
.smac-eyebrow {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--copper);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.smac-eyebrow::before {
  content: "";
  width: 24px;
  height: 1px;
  background: var(--copper);
}

/* monospace meta line */
.smac-meta {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-soft);
}

/* struct chat blocks */
.smac-struct-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--copper);
  margin-bottom: 6px;
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.smac-struct-label::before {
  content: "";
  width: 14px;
  height: 1px;
  background: var(--copper);
}
.smac-method-block {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px;
  color: var(--ink-soft);
  background: var(--paper);
  padding: 10px 14px;
  border: 1px dashed var(--line-soft);
  line-height: 1.6;
  margin-top: 6px;
}

/* greenwashing flag */
.smac-flag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--copper);
  letter-spacing: 0.04em;
}

/* reusable card - hover lift (add class smac-card to inline-HTML cards) */
.smac-card {
  border: 1px solid var(--line);
  background: var(--paper);
  transition: transform 0.15s ease, box-shadow 0.2s ease;
}
.smac-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

/* pill / tag */
.smac-pill {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--moss);
  border: 1px solid var(--line-soft);
  background: var(--paper);
  padding: 3px 10px;
}

/* "thinking" dots - reserve for when chat is wired to a real LLM */
.typing-dots { display: inline-flex; gap: 5px; align-items: center; }
.typing-dots span {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--copper);
  animation: smac-blink 1.2s infinite ease-in-out both;
}
.typing-dots span:nth-child(2) { animation-delay: 0.18s; }
.typing-dots span:nth-child(3) { animation-delay: 0.36s; }
@keyframes smac-blink {
  0%, 80%, 100% { opacity: 0.25; transform: translateY(0); }
  40% { opacity: 1; transform: translateY(-3px); }
}

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
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 11px !important;
  letter-spacing: 0.12em !important;
  text-transform: uppercase !important;
  color: var(--ink-soft) !important;
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
    """Small monospace tag/pill."""
    st.markdown(f'<span class="smac-pill">{text}</span>', unsafe_allow_html=True)


def spacer(px: int = 16):
    """Vertical whitespace."""
    st.markdown(f'<div style="height:{px}px"></div>', unsafe_allow_html=True)


def thinking():
    """Animated 'thinking...' indicator - use before a real-LLM reply streams in."""
    st.markdown(
        '<div class="typing-dots"><span></span><span></span><span></span></div>',
        unsafe_allow_html=True,
    )
