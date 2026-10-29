from __future__ import annotations
"""
Site-wide translation.

    from utils.i18n import t, sector_name
    st.markdown(t("overview.hero_title"))
    t("profile.rank_of", pos=3, n=37)          # placeholders use str.format names

Strings live in i18n/<lang>.json, one flat dict per language keyed like
"page.what". English (i18n/en.json) is the source of truth: a key missing from
another language falls back to English, and a key missing from English shows
the key itself, so a gap is visible but never crashes a page.

The active language is kept in st.session_state["lang"] and mirrored to the
?lang= URL parameter, so it survives a reload and a shared link opens in the
same language. language_switcher() (called once in app.py) renders the picker
in the top-right corner of every page.

Data values are never translated: jurisdiction and facility names, figures,
and passages quoted from source documents stay as they are.
"""

import json
from functools import lru_cache
from pathlib import Path

import streamlit as st

I18N_DIR = Path(__file__).parent.parent / "i18n"

# Order = order in the picker. Native names, so people can find their own language.
LANGS: dict[str, str] = {
    "en": "English",
    "zh": "中文",
    "es": "Español",
    "pt": "Português",
    "ko": "한국어",
    "hi": "हिन्दी",
}
DEFAULT = "en"

# English names, for telling the chat model which language to answer in.
LANG_ENGLISH_NAME = {
    "en": "English", "zh": "Simplified Chinese", "es": "Spanish",
    "pt": "Brazilian Portuguese", "ko": "Korean", "hi": "Hindi",
}


@lru_cache(maxsize=None)
def _strings(lang: str) -> dict:
    try:
        return json.loads((I18N_DIR / f"{lang}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def current_lang() -> str:
    lang = st.session_state.get("lang")
    if lang not in LANGS:
        q = st.query_params.get("lang")
        lang = q if q in LANGS else DEFAULT
        st.session_state["lang"] = lang
    return lang


def t(key: str, **kw) -> str:
    """Translated string for `key` in the active language (English fallback)."""
    lang = current_lang()
    s = _strings(lang).get(key)
    if s is None:
        s = _strings(DEFAULT).get(key, key)
    if kw:
        try:
            return s.format(**kw)
        except (KeyError, IndexError, ValueError):
            # a translation with a broken placeholder must not take the page down
            return _strings(DEFAULT).get(key, key).format(**kw)
    return s


def t_en(key: str, **kw) -> str:
    """English version regardless of the active language (e.g. for search text)."""
    s = _strings(DEFAULT).get(key, key)
    return s.format(**kw) if kw else s


def sector_name(sector: str) -> str:
    """Display name for one of the 8 sector categories (data keys stay English)."""
    return t(f"sector.{sector}") if f"sector.{sector}" in _strings(DEFAULT) else sector


def month_name(m: int) -> str:
    return t(f"month.{int(m)}")


def _has(key: str) -> bool:
    return key in _strings(DEFAULT)


def country_name(iso: str, fallback: str | None = None) -> str:
    """SMAC countries have translated names; any other country (Global View)
    keeps the name it came with."""
    return t(f"country.{iso}") if _has(f"country.{iso}") else (fallback or iso)


def region_name(region: str) -> str:
    return t(f"region.{region}") if _has(f"region.{region}") else region


def subunit_name(kind: str, n: int = 1) -> str:
    """'state' / 'states', 'province' / 'provinces' … in the active language."""
    key = f"subunit.{kind}" + ("" if n == 1 else ".pl")
    return t(key) if _has(key) else kind


def subsector_name(slug: str) -> str:
    """'enteric-fermentation-cattle-pasture' -> its display name in the active language."""
    k = f"subsector.{slug}"
    return t(k) if _has(k) else " ".join(w.capitalize() for w in str(slug).split("-"))


def tk(key: str, english: str, **kw) -> str:
    """Translate generated content (policy text, action bullets) whose English
    lives in the source code: returns `english` itself when no key exists, so
    adding new English content never shows a raw key."""
    return t(key, **kw) if _has(key) else (english.format(**kw) if kw else english)


def lang_name_for_llm() -> str:
    return LANG_ENGLISH_NAME[current_lang()]


def _on_change():
    st.session_state["lang"] = st.session_state["_lang_picker"]
    st.query_params["lang"] = st.session_state["lang"]


def language_switcher() -> None:
    """Compact picker, right-aligned at the top of the page. Call once per run
    (app.py does), before the page renders."""
    lang = current_lang()
    if st.query_params.get("lang") != lang:
        st.query_params["lang"] = lang
    _, right = st.columns([6, 1])
    with right:
        st.selectbox(
            "Language", options=list(LANGS), index=list(LANGS).index(lang),
            format_func=lambda k: f"🌐 {LANGS[k]}", key="_lang_picker",
            label_visibility="collapsed", on_change=_on_change,
        )
