from __future__ import annotations
"""
Optional LLM enrichment layer for the Methane Specialist chat.

The scripted response builder in chat_engine.py remains the source of truth
for every NUMBER shown (KPIs, rankings, GWP conversions) — those are always
computed directly from the data, never from the model. This module only
rewrites a few narrative blocks (Summary, Policy Context, Recommended
Mitigation Pathway) into richer prose, grounded in:
  - the same computed facts the scripted templates use (passed in explicitly,
    so the model can't invent a number that contradicts the KPI cards)
  - the RAG-retrieved reference excerpts (utils/rag.py) for the selected
    jurisdiction + output type
  - the user's actual question

No API key configured -> has_llm() is False -> chat_engine.py keeps using
the scripted templates untouched. Same if the call errors or returns
something we can't parse. This is additive, never a hard dependency.
"""

import json
import os
import re

MODEL = "claude-sonnet-5"
MAX_TOKENS = 1200
TIMEOUT_SEC = 25

TARGET_LABELS = ["Summary", "Policy Context", "Recommended Mitigation Pathway"]

SYSTEM_PROMPT = """You are the SMAC Methane Specialist, a data-grounded assistant for the \
Subnational Methane Action Coalition (SMAC). You help subnational governments understand \
their methane emissions and plan mitigation action.

Rules:
- Use ONLY the facts and reference excerpts provided to you. Never invent a number, date, \
policy name, or citation that isn't given to you.
- If the reference excerpts contain something directly relevant to the user's question, \
draw on it explicitly and naturally (you don't need to use every excerpt).
- If the reference excerpts are generic (not specific to this jurisdiction), say so plainly \
rather than implying they're jurisdiction-specific.
- Keep the tone concise, analytical, and non-promotional — this is a policy research tool, \
not marketing copy.
- Never fabricate a source, a real named individual's quote, or a regulatory claim.
- Output ONLY a JSON object mapping each requested section name to its rewritten text (plain \
prose or markdown bullets, 2-5 sentences per section). No text outside the JSON object."""


def has_llm() -> bool:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def _extract_json(text: str) -> dict | None:
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except (json.JSONDecodeError, ValueError):
                return None
    return None


OPEN_ANSWER_SYSTEM_PROMPT = """You are the SMAC Methane Specialist, a data-grounded assistant \
for the Subnational Methane Action Coalition (SMAC). You help subnational governments \
understand their methane emissions and plan mitigation action.

You are answering a real, specific question from the user — not filling in a fixed template. \
Write the answer that actually responds to what they asked, organized however best serves \
that question (short prose, a few bullets, a brief structure with your own headers if useful \
— whatever fits, don't force unrelated sections in just to be thorough).

Rules:
- Use ONLY the facts and reference excerpts provided to you. Never invent a number, date, \
policy name, or citation that isn't given to you.
- If the reference excerpts are flagged as general/not jurisdiction-specific, don't present \
them as this jurisdiction's own data — you can still draw on them for general best-practice \
framing if relevant, but say so.
- If the facts and references don't fully answer the question, say plainly what's missing \
rather than guessing or padding.
- Keep the tone concise, analytical, and non-promotional — this is a policy research tool, \
not marketing copy. Roughly 150-350 words unless the question genuinely needs more.
- Never fabricate a source, a real named individual's quote, or a regulatory claim.
- Output plain markdown — no JSON, no preamble like "Here's the answer", just the response \
itself."""


def generate_open_answer(
    user_text: str,
    facts: dict,
    rag_context: str,
    jurisdiction_label: str,
) -> str | None:
    """
    A free-form answer to the user's actual question, grounded in `facts`
    (computed numbers, never touched otherwise) and `rag_context` (retrieved
    reference excerpts). Unlike enrich_narrative_blocks, this does NOT force
    the response into a fixed set of labeled sections — RAG here only
    supplies material, it doesn't dictate the answer's shape.
    Returns None if no key configured or the call fails for any reason
    (caller falls back to the scripted templates).
    """
    if not user_text.strip() or not has_llm():
        return None

    import anthropic

    facts_str = "\n".join(f"- {k}: {v}" for k, v in facts.items())
    user_prompt = f"""Jurisdiction: {jurisdiction_label}
User's question: "{user_text}"

Computed facts (ground truth — also shown to the user in a data card alongside your answer):
{facts_str}

Reference excerpts retrieved from SMAC's document library:
{rag_context if rag_context else "(none retrieved for this query)"}

Answer the user's question directly."""

    try:
        client = anthropic.Anthropic(timeout=TIMEOUT_SEC)
        resp = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=OPEN_ANSWER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        ).strip()
        return text or None
    except Exception:
        # network error, bad key, rate limit, timeout, etc. — fail silently,
        # caller falls back to the scripted templates
        return None


def enrich_narrative_blocks(
    original_blocks: dict[str, str],
    user_text: str,
    facts: dict,
    rag_context: str,
    jurisdiction_label: str,
) -> dict[str, str] | None:
    """
    original_blocks: {label: current_scripted_text} for whichever of
        TARGET_LABELS are present in this response (varies by output type).
    facts: computed numbers already shown in the Key Data Insight block
        (year totals, YoY, rank, top sectors, etc.) — passed as plain text
        so the model grounds its writing in the same figures the KPI cards
        show, without being able to silently contradict them.
    Returns {label: new_text} for the labels it successfully rewrote, or
    None if the call failed / wasn't parseable (caller keeps the originals).
    """
    if not original_blocks or not has_llm():
        return None

    import anthropic

    sections_str = "\n\n".join(
        f"### {label} (current draft)\n{content}" for label, content in original_blocks.items()
    )
    facts_str = "\n".join(f"- {k}: {v}" for k, v in facts.items())

    user_prompt = f"""Jurisdiction: {jurisdiction_label}
User's question: "{user_text}"

Computed facts (already shown to the user elsewhere on this page — treat as ground truth):
{facts_str}

Reference excerpts retrieved from SMAC's document library (may or may not be specific to \
this jurisdiction — see the [tag] before each one):
{rag_context if rag_context else "(none retrieved for this query)"}

Rewrite the following sections to better answer the user's actual question, grounded in the \
facts and reference excerpts above:

{sections_str}

Return a JSON object with exactly these keys: {json.dumps(list(original_blocks.keys()))}"""

    try:
        client = anthropic.Anthropic(timeout=TIMEOUT_SEC)
        resp = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = "".join(block.text for block in resp.content if getattr(block, "type", None) == "text")
        parsed = _extract_json(raw)
        if not isinstance(parsed, dict):
            return None
        # only accept keys we actually asked for, and non-empty string values
        out = {
            k: v for k, v in parsed.items()
            if k in original_blocks and isinstance(v, str) and v.strip()
        }
        return out or None
    except Exception:
        # network error, bad key, rate limit, timeout, etc. — fail silently,
        # caller keeps the scripted blocks
        return None
