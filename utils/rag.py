from __future__ import annotations
"""
Local RAG (retrieval-augmented generation) over SMAC's internal methane
action-plan library — no external embedding API, no vector DB. Pure-Python
BM25 over pre-chunked text (see scripts/build_rag_index.py for how
data/rag_corpus.json was built from the raw source documents).

Designed so the Chat page's existing sidebar selections (jurisdiction +
output type) become retrieval FILTERS, not just prompt decoration — narrowing
the candidate pool before ranking is what will make this genuinely useful
once the backend is swapped for a real LLM: the same two selections can be
reused to build the system-prompt context for that model.
"""

import json
import math
import re
from collections import Counter
from pathlib import Path

import streamlit as st

RAG_CORPUS_PATH = Path(__file__).parent.parent / "data" / "rag_corpus.json"

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are",
    "was", "were", "be", "by", "with", "as", "at", "this", "that", "these",
    "those", "it", "its", "from", "will", "shall", "which", "into", "such",
    "may", "can", "not", "than", "then", "also",
}


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9\-]{1,}", text.lower())
    return [w for w in words if w not in _STOPWORDS]


def has_rag_corpus() -> bool:
    return RAG_CORPUS_PATH.exists()


@st.cache_resource(show_spinner=False)
def _load_index():
    """Load chunks + build BM25 statistics once per app run."""
    with open(RAG_CORPUS_PATH, encoding="utf-8") as f:
        chunks = json.load(f)

    tokenized = [_tokenize(c["text"]) for c in chunks]
    doc_lens = [len(t) for t in tokenized]
    avgdl = sum(doc_lens) / max(len(doc_lens), 1)

    df = Counter()
    for toks in tokenized:
        df.update(set(toks))
    n_docs = len(chunks)
    idf = {
        term: math.log(1 + (n_docs - freq + 0.5) / (freq + 0.5))
        for term, freq in df.items()
    }

    term_freqs = [Counter(toks) for toks in tokenized]

    return {
        "chunks": chunks,
        "term_freqs": term_freqs,
        "doc_lens": doc_lens,
        "avgdl": avgdl,
        "idf": idf,
    }


def _bm25_score(query_terms: list[str], idx: int, index, k1: float = 1.5, b: float = 0.75) -> float:
    tf = index["term_freqs"][idx]
    dl = index["doc_lens"][idx]
    avgdl = index["avgdl"]
    score = 0.0
    for term in query_terms:
        f = tf.get(term, 0)
        if f == 0:
            continue
        idf = index["idf"].get(term, 0.0)
        denom = f + k1 * (1 - b + b * dl / max(avgdl, 1e-9))
        score += idf * (f * (k1 + 1)) / max(denom, 1e-9)
    return score


def rag_search(
    query: str,
    iso: str | None = None,
    location: str | None = None,
    output_type: str | None = None,
    k: int = 4,
    min_score: float = 0.5,
) -> list[dict]:
    """
    Retrieve the top-k chunks for `query`, filtered by jurisdiction/output type
    where possible. Filtering degrades gracefully: if the exact (iso, location)
    has no indexed material, falls back to iso-only, then to the unfiltered
    corpus — so a jurisdiction with no local documents still gets the general
    solution-bank / template material rather than nothing.
    Returns [] if nothing clears `min_score` (caller should treat that as "no
    grounded material" rather than force a low-quality citation).
    """
    if not has_rag_corpus():
        return []
    index = _load_index()
    chunks = index["chunks"]

    def candidate_indices(require_loc: bool, require_output: bool):
        out = []
        for i, c in enumerate(chunks):
            if require_loc:
                if location and c["location"] != location:
                    continue
                if not location and iso and c["iso3"] != iso:
                    continue
            if require_output and output_type and output_type not in c["output_types"]:
                continue
            out.append(i)
        return out

    # progressively widen the filter until we have candidates to rank
    candidates = candidate_indices(require_loc=True, require_output=True)
    if not candidates:
        candidates = candidate_indices(require_loc=True, require_output=False)
    if not candidates:
        candidates = candidate_indices(require_loc=False, require_output=True)
    if not candidates:
        candidates = list(range(len(chunks)))

    query_terms = _tokenize(query)
    if not query_terms:
        return []

    scored = [(idx, _bm25_score(query_terms, idx, index)) for idx in candidates]
    scored = [(idx, s) for idx, s in scored if s >= min_score]
    scored.sort(key=lambda x: x[1], reverse=True)

    results = []
    for idx, score in scored[:k]:
        c = chunks[idx]
        results.append({
            "text": c["text"],
            "source_file": c["source_file"],
            "source_path": c["source_path"],
            "iso3": c["iso3"],
            "location": c["location"],
            "tier": c["tier"],
            "sector": c["sector"],
            "score": round(score, 2),
        })
    return results


def format_rag_context(results: list[dict]) -> str:
    """Render retrieved chunks as a citation-tagged context block — usable both
    inline in the current scripted chat and as the context section of a system
    prompt once this is wired to a real LLM backend."""
    if not results:
        return ""
    lines = []
    for r in results:
        tag = r["location"] or r["tier"].replace("_", " ")
        lines.append(f"[{tag} · {r['source_file']}] {r['text']}")
    return "\n\n".join(lines)
