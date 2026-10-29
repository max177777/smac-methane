from __future__ import annotations
"""
Scripted chat response builder.
Two modes:
  - 'methane'  : structured 5-block response grounded in real data
  - 'general'  : conversational free-form scripted response
"""

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from utils.data_loader import (
    COUNTRY_META, COUNTRY_ORDER, country_yearly, country_monthly, location_monthly,
    location_yearly_ranking, location_sectors, sector_yearly_series, SECTOR_ORDER,
    fmt_int, pct_change, CURRENT_YEAR, DATA_RANGE_LABEL,
)
from utils.policy_content import POLICY, PATHWAYS, GWP100, GWP20
from utils.rag import rag_search, format_rag_context
from utils.llm import has_llm, generate_open_answer, enrich_narrative_blocks
from utils.i18n import t, tk, sector_name, country_name, month_name, lang_name_for_llm, current_lang


def _pw(iso: str, i: int, field: str, english: str, j: int | None = None) -> str:
    """Translated PATHWAYS text (sector / flag / action j) — English if no key."""
    key = f"pathway.{iso}.{i}.{field}" + (f".{j}" if j is not None else "")
    return tk(key, english)

LLM_TARGET_LABELS = {"Summary", "Policy Context", "Recommended Mitigation Pathway"}


@dataclass
class MethaneContext:
    iso: str
    location: str  # "__all__" or specific name
    metric: str    # "ch4" | "gwp100" | "gwp20"
    output: str = "data"   # only used as a fallback template selector when no LLM is available
    year: str = "all"      # "all" or a specific year as string, e.g. "2024"
    sector: str = "all"    # "all" or one of data_loader.SECTOR_ORDER


@dataclass
class ChatBlock:
    """A single block of a structured response."""
    label: str
    content: str  # markdown
    is_method: bool = False


@dataclass
class ChatChart:
    """One visualization attached to a response. `kind` tells the page which
    renderer to use; `data` is whatever that renderer needs."""
    kind: str          # "timeseries" | "sector_bar" | "ranking_bar" | "yoy_bar" | "sector_trend"
    caption: str
    data: object = None


@dataclass
class MethaneResponse:
    blocks: list[ChatBlock]
    chart_df = None  # legacy single time series — kept for backwards compatibility
    chart_subject: str = ""
    charts: list = None  # list[ChatChart], picked to match the question


# ============================================================
# UTILS
# ============================================================
def _metric_factor(metric: str) -> tuple[float, str, str]:
    if metric == "gwp100":
        return GWP100, "t CO₂e", "CO₂e (GWP100)"
    if metric == "gwp20":
        return GWP20, "t CO₂e", "CO₂e (GWP20)"
    return 1.0, "t CH₄", "CH₄"


def _detect_mode_from_text(user_text: str, current_output: str) -> str:
    txt = user_text.lower()
    if re.search(r"gwp|co2e|co₂e|warming pot", txt):
        return "method"
    if re.search(r"polic|regulat|rule|law|legislation", txt):
        return "policy"
    if re.search(r"mitigat|reduce|pathway|abat|action", txt):
        return "pathway"
    if re.search(r"trend|over time|grow|increas|decreas|monthly|seasonal", txt):
        return "trend"
    return current_output


_MDE_CSV = Path(__file__).parent.parent / "data" / "MD_official_inventory_ch4.csv"


def _mde_inventory_summary(iso: str, location: str | None) -> str | None:
    """Maryland's own MDE inventory covers 2006-2020 — years Climate TRACE
    doesn't reach. Surfaced as a fact so the model can offer the nearest
    available year instead of saying nothing pre-2021 exists."""
    if iso != "USA" or location != "Maryland" or not _MDE_CSV.exists():
        return None
    try:
        df = pd.read_csv(_MDE_CSV)
        totals = df.groupby("year")["ch4_tonnes"].sum().sort_index()
    except Exception:
        return None
    if totals.empty:
        return None
    series = ", ".join(f"{int(y)}: {v:,.0f} t" for y, v in totals.items())
    return (
        f"Maryland Department of the Environment (MDE) official state GHG "
        f"inventory, CH4 totals — {series}. This is a SEPARATE, bottom-up "
        f"source from Climate TRACE and covers different years; the two are "
        f"compiled differently and do not necessarily agree. MDE DOES cover "
        f"each of the years listed above — if the user asks about one of them, "
        f"that figure is available and should be given. MDE does not publish "
        f"figures for years not listed."
    )


# Questions about the assistant itself ("how do you work", "what can you do")
# and bare pleasantries are NOT data questions. Attaching retrieved documents
# and a time-series chart to them produced the worst output this tool has had —
# asking "can you explain how you work" returned three pages of county
# composting guidance and an emissions chart, none of it relevant.
_META_RE = re.compile(
    r"\b("
    r"how (do|does|did) (you|this|it|the (tool|site|chat))\b"
    r"|what (can|do) (you|this|it) (do|cover|know|use|have)\b"
    r"|who (are|made) you\b|what are you\b"
    r"|explain (yourself|how you|what you)\b"
    r"|your (capabilit|source|limitation|method|data source)"
    r"|where (do|does) (you|your data|the data) come from\b"
    r"|are you (an? )?(ai|bot|llm|human)\b"
    r"|how (accurate|reliable|current) are you\b"
    r"|^(hi|hey|hello|thanks|thank you|help)\b"
    r")",
    re.I,
)

# Signals that the question is actually about emissions / policy / a place,
# i.e. the kind of question retrieved documents and a chart genuinely serve.
_DATA_RE = re.compile(
    r"\b("
    r"emission|methane|ch4|co2e|gwp|tonne|ton\b|mt\b|kt\b"
    r"|sector|source|landfill|waste|agricultur|livestock|manure|enteric"
    r"|oil|gas|coal|mining|power|industr|transport|building"
    r"|trend|compare|comparison|rank|top|highest|biggest|largest"
    r"|policy|policies|regulat|plan|action|mitigat|reduc|target|pledge"
    r"|inventory|facility|facilities|plant|site"
    r"|\b(19|20)\d{2}\b"
    r")",
    re.I,
)


def _question_intent(user_text: str, *, place_names: tuple[str, ...] = ()) -> str:
    """'meta' -> about the tool itself; 'data' -> about emissions/policy/places;
    'other' -> neither (short or ambiguous follow-up). Only 'data' questions get
    retrieved documents and charts attached.

    `place_names` lets a question that names the jurisdiction count as a data
    question even with no topic keyword — "tell me about Alberta" has no
    emissions vocabulary in it but plainly wants the data.
    """
    txt = (user_text or "").strip()
    if not txt:
        return "other"
    if _META_RE.search(txt):
        return "meta"
    if _DATA_RE.search(txt):
        return "data"
    low = txt.lower()
    if any(p and p.lower() in low for p in place_names):
        return "data"
    return "other"


def _select_charts(user_text: str, *, iso: str, location: str | None, is_loc: bool,
                   monthly, rank, target_year: int, subject: str,
                   sector_filter: str | None) -> list:
    """
    Pick the visualizations that actually fit the question. Everything here is
    built from data we already have loaded — no new data sources. Falls back to
    the monthly time series so there's always at least one chart.
    """
    txt = user_text.lower()
    charts: list[ChatChart] = []

    wants_sector = bool(re.search(
        r"sector|source|where.*from|breakdown|compos|landfill|agricultur|waste|"
        r"oil|gas|livestock|manure|energy|industr|transport", txt))
    wants_ranking = bool(re.search(
        r"top|rank|biggest|largest|highest|worst|compare.*(state|province|region|jurisdiction)|"
        r"which .*(state|province|region|jurisdiction)", txt))
    wants_trend = bool(re.search(
        r"trend|over time|change|grow|increas|decreas|rising|falling|monthly|"
        r"season|year.over.year|yoy|history|since", txt))

    # --- sector composition, when the question is about sources/sectors ---
    if wants_sector and is_loc:
        sec = location_sectors(iso, location, target_year)
        sec = sec[sec["total_emission"] > 0]
        if not sec.empty:
            charts.append(ChatChart(
                kind="sector_bar",
                caption=t("compare.by_sector", label=subject, y=target_year),
                data=sec,
            ))

    # --- subnational ranking, when the question is comparative ---
    if wants_ranking and not rank.empty and len(rank) > 1:
        top = rank.head(10)[["location", "ch4_tonnes_year"]].copy()
        charts.append(ChatChart(
            kind="ranking_bar",
            caption=t("chat.cap_ranking", n=len(top), country=country_name(iso), y=target_year),
            data=top,
        ))

    # --- year-over-year movers, for "who changed most" style questions ---
    if wants_ranking and wants_trend and not rank.empty and "yoy_pct" in rank.columns:
        movers = rank.dropna(subset=["yoy_pct"]).head(10)[["location", "yoy_pct"]].copy()
        if len(movers) > 1:
            charts.append(ChatChart(
                kind="yoy_bar",
                caption=t("chat.cap_yoy", y=target_year),
                data=movers,
            ))

    # --- sector composition over time, when asking how the mix shifted ---
    if wants_sector and wants_trend and is_loc:
        trend_df = sector_yearly_series(iso, location)
        trend_df = trend_df[trend_df["ch4_tonnes"] > 0]
        if not trend_df.empty:
            charts.append(ChatChart(
                kind="sector_trend",
                caption=t("chat.cap_sector_trend", subject=subject),
                data=trend_df,
            ))

    # --- always keep the monthly series if nothing else fired, or if the
    #     question is explicitly about the trend ---
    # Fall back to the monthly series only for questions a chart actually
    # serves — a question about the tool itself gets no chart at all.
    if wants_trend or (not charts and _question_intent(
            user_text, place_names=(subject, COUNTRY_META[iso]["name"])) == "data"):
        charts.insert(0, ChatChart(
            kind="timeseries",
            caption=t("chat.cap_monthly", subject=subject, range=DATA_RANGE_LABEL),
            data=monthly,
        ))

    return charts[:3]  # cap so a reply never turns into a wall of charts


# ============================================================
# METHANE SPECIALIST RESPONSE
# ============================================================
def build_methane_response(user_text: str, ctx: MethaneContext) -> MethaneResponse:
    global L_SUMMARY, L_INSIGHT, L_POLICY, L_PATHWAY, L_METHOD
    L_SUMMARY, L_INSIGHT, L_POLICY = t("chat.lbl_summary"), t("chat.lbl_insight"), t("chat.lbl_policy")
    L_PATHWAY, L_METHOD = t("chat.lbl_pathway"), t("chat.lbl_method")
    mult, unit, metric_label = _metric_factor(ctx.metric)
    iso = ctx.iso
    meta = COUNTRY_META[iso]
    country_name_ = country_name(iso)
    subunit_type = meta["subunit_type"]

    # CLEAR "Locate in Time": a specific year pins every KPI/ranking below to
    # that year instead of the site-wide CURRENT_YEAR default. "all" keeps
    # today's default behavior unchanged.
    target_year = int(ctx.year) if ctx.year and ctx.year != "all" else CURRENT_YEAR
    sector_filter = ctx.sector if ctx.sector and ctx.sector != "all" else None

    # Pick the data slice
    is_loc = ctx.location != "__all__"
    if is_loc:
        monthly = location_monthly(iso, ctx.location)
        yearly = monthly.groupby("year", as_index=False)["ch4_tonnes"].sum()
        subject = ctx.location
    else:
        monthly = country_monthly(iso)
        yearly = country_yearly(iso)
        subject = country_name_

    # Yearly aggregates
    def y(year):
        row = yearly[yearly["year"] == year]
        return float(row["ch4_tonnes"].iloc[0]) if len(row) else 0.0

    y21 = y(2021)
    y_prior = y(target_year - 1)
    y_now = y(target_year)
    yoy = pct_change(y_now, y_prior)
    drift = pct_change(y_now, y21)
    n_years = max(target_year - 2021, 1)

    # Subnational ranking for context
    rank = location_yearly_ranking(iso, year=target_year)
    total = rank["ch4_tonnes_year"].sum()
    top3_names = rank["location"].head(3).tolist()
    top3_share = rank.head(3)["share"].sum()

    # CLEAR "Context": a specific sector pulls that sector's own share of this
    # jurisdiction's total, shown alongside the aggregate CH4 figures.
    sector_insight = None
    if sector_filter and is_loc:
        sec_df = location_sectors(iso, ctx.location, target_year)
        sec_row = sec_df[sec_df["sector"] == sector_filter]
        if len(sec_row) and y_now > 0:
            sec_tonnes = float(sec_row["total_emission"].iloc[0])
            sector_insight = t("chat.sector_insight", sector=sector_name(sector_filter),
                               t=fmt_int(sec_tonnes), y=target_year,
                               pct=f"{sec_tonnes / y_now * 100:.1f}", subject=subject)

    # ---------- REFERENCE LIBRARY RETRIEVAL (local RAG) ----------
    # Runs BEFORE any answer is written — RAG's job here is purely to find
    # material (filtered by jurisdiction + sector), not to dictate the shape
    # of the response. Both the open-ended LLM answer and the scripted
    # fallback below use the same retrieved excerpts.
    #
    # Skipped entirely for questions about the tool itself: retrieval will
    # always return *something* (BM25 ranks, it doesn't judge relevance), so
    # without this gate "how do you work" got three pages of county composting
    # guidance stapled underneath.
    intent = _question_intent(user_text, place_names=(subject, country_name_))
    if intent == "meta":
        rag_hits = []
    else:
        rag_hits = rag_search(
            user_text,
            iso=iso,
            location=ctx.location if is_loc else None,
            sector=sector_filter,
            k=3,
        )
    rag_context = format_rag_context(rag_hits)
    has_dedicated_refs = is_loc and any(h["location"] == ctx.location for h in rag_hits)
    if rag_hits and not has_dedicated_refs:
        # Flag this for the LLM too — without this, the model has no way to know
        # these excerpts are generic/from a different jurisdiction, and could
        # blend them into the answer as if they were {subject}'s own data.
        llm_rag_context = (
            f"NOTE: none of the excerpts below are specific to {subject} — they're "
            f"the closest general matches from the reference library. Do not present "
            f"them as {subject}'s own data or documents; you may still draw on them "
            f"for general best-practice framing if relevant.\n\n{rag_context}"
        )
    else:
        llm_rag_context = rag_context

    blocks: list[ChatBlock] = []

    # ---------- PRIMARY: open-ended LLM answer ----------
    # Actually responds to what the user asked, instead of filling in a fixed
    # 5-box template. RAG excerpts + computed facts are the only grounding —
    # the MODEL decides how to organize the answer, not us.
    answer = None
    if has_llm():
        # Pass the FULL year series, not just the selected year. Previously only
        # the selected year was sent, so when asked about a year we don't cover
        # the model would say "the dataset only covers <selected year>" — which
        # understated what's actually here and gave the user a wrong picture of
        # the tool's coverage.
        series = ", ".join(
            f"{int(r.year)}: {fmt_int(r.ch4_tonnes)} t"
            for r in yearly.sort_values("year").itertuples()
        )
        facts = {
            "jurisdiction": subject,
            "country": country_name_,
            "SOURCE 1 of N — Climate TRACE, CH4 total by year": series,
            "Climate TRACE coverage": (
                f"{DATA_RANGE_LABEL} only. This statement is about Climate TRACE "
                f"ONLY — other sources listed below may cover other years. Check "
                f"every source before telling the user a year is unavailable. "
                f"Never estimate or back-cast a year that no source covers."
            ),
            f"currently selected year ({target_year}) total CH4 (t)": fmt_int(y_now),
            "year-over-year change (%)": f"{yoy:+.2f}" if yoy == yoy else "n/a",
            f"{n_years}-year drift since 2021 (%)": f"{drift:+.2f}" if drift == drift else "n/a",
            "top 3 subunits nationally": ", ".join(top3_names) if top3_names else "n/a",
            "top 3 share of national total (%)": f"{top3_share:.1f}",
        }
        # Maryland additionally has its state's own bottom-up inventory loaded,
        # covering years Climate TRACE doesn't reach — surface it so the model
        # knows to offer it rather than claiming nothing pre-2021 exists.
        _mde = _mde_inventory_summary(iso, ctx.location if is_loc else None)
        if _mde:
            facts["SOURCE 2 of N — Maryland MDE official state inventory"] = _mde
        if sector_insight:
            facts["sector-specific insight"] = sector_insight
        answer = generate_open_answer(
            user_text, facts=facts, rag_context=llm_rag_context, jurisdiction_label=subject,
            language=lang_name_for_llm(),
        )

    if answer:
        blocks.append(ChatBlock(t("chat.lbl_answer"), answer))

        # The data card used to be appended unconditionally, which left a
        # template-shaped residue on answers that had nothing to do with the
        # selected year's headline figures (ask about 2006 and you'd still get
        # "2025 total / YoY / drift" bolted underneath). Now it only appears
        # when it adds something the answer doesn't already say — the model
        # owns the structure, this is just a verifiable figure receipt.
        # Suppress when it wouldn't help: either the answer already quotes the
        # figure, or the user asked about a DIFFERENT year than the one selected
        # (asking about 2006 and getting a 2025 card bolted underneath is the
        # template residue this card is supposed to avoid).
        already_stated = fmt_int(y_now * mult) in answer
        asked_years = {int(m.group(0))
                       for m in re.finditer(r"\b(?:19|20)\d{2}\b", user_text)}
        asks_other_year = bool(asked_years) and target_year not in asked_years
        # Also skip for questions about the tool itself — a figures card under
        # "how do you work" is the same template residue as the rest.
        if not already_stated and not asks_other_year and intent != "meta":
            insight = t("chat.figures_card", y=target_year, total=fmt_int(y_now * mult), unit=unit,
                        yoy=f"{yoy:+.2f}", n=n_years, drift=f"{drift:+.2f}")
            if sector_insight and sector_insight not in answer:
                insight += f"\n- {sector_insight}"
            blocks.append(ChatBlock(t("chat.lbl_figures", subject=subject, y=target_year), insight))

    else:
        # ---------- FALLBACK: scripted templates ----------
        # No API key configured, or the call failed for any reason — fall
        # back to the deterministic 5-block templates, same as before this
        # feature existed. Mode is auto-detected from the question text only
        # (there's no sidebar "output type" selector anymore).
        mode = _detect_mode_from_text(user_text, "data")

        # ---------- DATA ----------
        if mode == "data":
            if is_loc:
                share_of_nation = y_now / total * 100 if total else 0
                summary = t("chat.s_data_loc", y=target_year, subject=subject,
                            total=fmt_int(y_now * mult), unit=unit, metric=metric_label,
                            pct=f"{share_of_nation:.2f}", country=country_name_)
                insight = t("chat.s_data_loc_insight", base=fmt_int(y21 * mult), unit=unit,
                            py=target_year - 1, prior=fmt_int(y_prior * mult), y=target_year,
                            now=fmt_int(y_now * mult), yoy=f"{yoy:+.2f}",
                            dir=t("chat.rising") if yoy > 0 else t("chat.falling"),
                            n=n_years, drift=f"{drift:+.2f}")
            else:
                summary = t("chat.s_data_country", y=target_year, country=country_name_,
                            total=fmt_int(y_now * mult), unit=unit, top3=", ".join(top3_names),
                            pct=f"{top3_share:.1f}")
                top5 = rank.head(5)
                insight = t("chat.s_top_units", y=target_year) + "\n\n" + "\n".join(
                    f"- **{r.location}** — {fmt_int(r.ch4_tonnes_year)} t ({r.share:.1f}%)"
                    for r in top5.itertuples()
                )

            blocks.append(ChatBlock(L_SUMMARY, summary))
            if sector_insight:
                insight = insight + f"\n- {sector_insight}"
            blocks.append(ChatBlock(L_INSIGHT, insight))
            blocks.append(ChatBlock(L_POLICY, tk(f"policy.{iso}.summary", POLICY[iso]["summary"])))
            path = PATHWAYS.get(iso, [])
            if path:
                actions = " · ".join(f"*{_pw(iso, 0, 'action', a, j)}*"
                                     for j, a in enumerate(path[0]["actions"][:3]))
                blocks.append(ChatBlock(
                    L_PATHWAY,
                    t("chat.s_data_pathway", sector=_pw(iso, 0, "sector", path[0]["sector"]), actions=actions)
                ))
            blocks.append(ChatBlock(
                L_METHOD,
                t("chat.s_data_method", range=DATA_RANGE_LABEL, metric=metric_label, mult=f"{mult:g}"),
                is_method=True
            ))

        # ---------- TREND ----------
        elif mode == "trend":
            peak_idx = monthly["ch4_tonnes"].idxmax()
            trough_idx = monthly["ch4_tonnes"].idxmin()
            peak = monthly.loc[peak_idx]
            trough = monthly.loc[trough_idx]
            summary = t("chat.s_trend", range=DATA_RANGE_LABEL, subject=subject,
                        dir=t("chat.rising") if drift > 0 else t("chat.falling"),
                        drift=f"{drift:+.2f}", yoy=f"{yoy:+.2f}")
            insight = t("chat.s_trend_insight",
                        peak_m=month_name(peak["month"]), peak_y=int(peak["year"]),
                        peak_t=fmt_int(peak["ch4_tonnes"]),
                        low_m=month_name(trough["month"]), low_y=int(trough["year"]),
                        low_t=fmt_int(trough["ch4_tonnes"]),
                        ratio=f"{peak['ch4_tonnes'] / trough['ch4_tonnes']:.2f}",
                        avg=f"{drift / max(n_years, 1):+.2f}")
            policy_ctx = t("chat.s_trend_rising") if drift > 0 else t("chat.s_trend_falling")

            blocks.append(ChatBlock(L_SUMMARY, summary))
            blocks.append(ChatBlock(L_INSIGHT, insight))
            blocks.append(ChatBlock(L_POLICY, policy_ctx))
            path = PATHWAYS.get(iso, [])
            if path:
                blocks.append(ChatBlock(
                    L_PATHWAY,
                    " · ".join(f"*{_pw(iso, 0, 'action', a, j)}*" for j, a in enumerate(path[0]["actions"]))
                ))
            blocks.append(ChatBlock(L_METHOD, t("chat.s_trend_method"), is_method=True))

        # ---------- POLICY ----------
        elif mode == "policy":
            p = POLICY[iso]
            from utils.i18n import subunit_name
            blocks.append(ChatBlock(L_SUMMARY, t("chat.s_policy", country=country_name_)))
            top3_total = rank.head(3)["ch4_tonnes_year"].sum()
            blocks.append(ChatBlock(
                L_INSIGHT,
                t("chat.s_policy_insight", y=target_year, top3=", ".join(top3_names),
                  t=fmt_int(top3_total), pct=f"{top3_share:.1f}", unit=subunit_name(subunit_type, 2))
            ))
            policy_text = "\n\n".join(
                f"**{tk(f'policy.{iso}.{i}.name', n)}.** {tk(f'policy.{iso}.{i}.desc', d)}"
                for i, (n, d) in enumerate(p["policies"]))
            blocks.append(ChatBlock(L_POLICY, policy_text))
            path = PATHWAYS.get(iso, [])
            if path:
                actions = " · ".join(f"*{_pw(iso, 0, 'action', a, j)}*" for j, a in enumerate(path[0]["actions"]))
                blocks.append(ChatBlock(
                    L_PATHWAY,
                    t("chat.s_policy_pathway", unit=subunit_name(subunit_type, 1), actions=actions)
                ))
            blocks.append(ChatBlock(
                L_METHOD,
                t("chat.s_policy_method", flag=_pw(iso, 0, "flag", path[0]["flag"]) if path else "—"),
                is_method=True,
            ))

        # ---------- PATHWAY ----------
        elif mode == "pathway":
            path = PATHWAYS.get(iso, [])
            if not path:
                blocks.append(ChatBlock(L_SUMMARY, t("chat.s_no_pathway", country=country_name_)))
            else:
                secs = [_pw(iso, i, "sector", x["sector"]) for i, x in enumerate(path)]
                blocks.append(ChatBlock(
                    L_SUMMARY,
                    t("chat.s_pathway", subject=subject, s1=secs[0],
                      s2=secs[1] if len(secs) > 1 else "—", s3=secs[2] if len(secs) > 2 else "—")
                ))
                insight = t("chat.s_pathway_list") + "\n\n" + "\n".join(
                    f"- **{secs[i]}.** {' · '.join(_pw(iso, i, 'action', a, j) for j, a in enumerate(x['actions']))}"
                    for i, x in enumerate(path)
                )
                blocks.append(ChatBlock(L_INSIGHT, insight))
                blocks.append(ChatBlock(
                    L_POLICY,
                    t("chat.s_pathway_policy") + " " + tk(f"policy.{iso}.summary", POLICY[iso]["summary"])
                ))
                blocks.append(ChatBlock(
                    L_PATHWAY,
                    t("chat.s_pathway_first", action=_pw(iso, 0, "action", path[0]["actions"][0], 0),
                      sector=secs[0])
                ))
                flags = " / ".join(_pw(iso, i, "flag", x["flag"]) for i, x in enumerate(path))
                blocks.append(ChatBlock(L_METHOD, t("chat.s_pathway_method", flags=flags), is_method=True))

        # ---------- METHOD ----------
        else:  # method
            blocks.append(ChatBlock(L_SUMMARY, t("chat.s_method")))
            blocks.append(ChatBlock(L_INSIGHT, t(
                "chat.s_method_insight", subject=subject, t=fmt_int(y_now), y=target_year,
                g100=GWP100, v100=fmt_int(y_now * GWP100), g20=GWP20, v20=fmt_int(y_now * GWP20))))
            blocks.append(ChatBlock(L_POLICY, t("chat.s_method_policy")))
            blocks.append(ChatBlock(L_PATHWAY, t("chat.s_method_pathway")))
            blocks.append(ChatBlock(L_METHOD, t("chat.s_method_method"), is_method=True))

    # ---------- REFERENCE LIBRARY (local RAG) ----------
    if rag_hits:
        if has_dedicated_refs:
            blocks.append(ChatBlock(t("chat.lbl_library"), rag_context))
        else:
            note = t("chat.library_note", subject=subject) + "\n\n"
            blocks.append(ChatBlock(t("chat.lbl_library_general"), note + rag_context))

    response = MethaneResponse(blocks=blocks, chart_subject=subject)
    response.chart_df = monthly
    response.charts = _select_charts(
        user_text, iso=iso, location=ctx.location if is_loc else None, is_loc=is_loc,
        monthly=monthly, rank=rank, target_year=target_year, subject=subject,
        sector_filter=sector_filter,
    )
    return response


# ============================================================
# GENERAL ASSISTANT — scripted conversational
# ============================================================
GENERAL_PATTERNS = [
    (re.compile(r"\b(hello|hi|hey|hola)\b", re.I),
     "Hello — I'm the general-purpose side of SMAC. Ask me anything; if it turns out to be "
     "methane-related you might prefer the Methane Specialist tab on the left, but for everything "
     "else I'm here."),

    (re.compile(r"climate change|global warming", re.I),
     "Climate change is the long-term shift in temperature and weather patterns driven primarily "
     "by greenhouse gases — carbon dioxide, methane, nitrous oxide, fluorinated gases — that "
     "human activity has added to the atmosphere since the industrial revolution. Energy "
     "production, deforestation, agriculture, and waste are the main contributors.\n\n"
     "The mainstream framing now used by the IPCC is to keep warming \"well below 2°C\" with "
     "efforts toward 1.5°C above pre-industrial levels. Each fraction of a degree maps to "
     "measurable differences in heatwaves, sea-level rise, biodiversity loss, and economic damage."),

    (re.compile(r"methane molecule|how does methane warm|greenhouse effect", re.I),
     "The short version: methane (CH₄) absorbs infrared radiation that the Earth's surface "
     "re-emits. Specifically, the C–H bonds vibrate at frequencies that overlap with the "
     "wavelengths leaving the surface, so each CH₄ molecule intercepts that energy and "
     "re-radiates some of it back downward instead of letting it escape to space.\n\n"
     "Methane is a more potent absorber per molecule than CO₂ because its vibrational modes are "
     "well-placed in the atmospheric \"window\" — wavelengths where CO₂ doesn't already saturate. "
     "But it has a much shorter lifetime in the atmosphere (≈12 years), so its warming effect "
     "fades faster than CO₂'s. That trade-off is why short-term (GWP20) and long-term (GWP100) "
     "framings give different answers."),

    (re.compile(r"\bmethane\b", re.I),
     "Methane (CH₄) is a short-lived greenhouse gas that punches well above its weight: it's "
     "roughly 80 times more warming than CO₂ over a 20-year horizon, and about 27 times over "
     "100 years. It comes from oil & gas systems (leaks, venting, flaring), enteric fermentation "
     "in cattle, landfills, rice cultivation, and a few other sources.\n\n"
     "Because it dissipates from the atmosphere within a decade or so, cutting methane delivers "
     "near-term cooling that CO₂ reductions cannot. That's why it shows up in policy as a \"fast "
     "climate lever.\"\n\n"
     "If you want to dig into specific country data, switch to the Methane Specialist tab on the left."),

    (re.compile(r"\b(meeting|email)\b", re.I),
     "Sure — here's a clean draft you can adapt:\n\n"
     "*Subject:* Quick chat on [topic] next week?\n\n"
     "*Hi [name],*\n\n"
     "Hope you've had a good week. I wanted to see if you'd have 20-30 minutes next week to "
     "talk through [specific topic / question]. I think a short conversation will be more useful "
     "than a long email thread.\n\n"
     "Tuesday or Thursday afternoon work best on my end, but I'm flexible — just let me know what "
     "fits your schedule.\n\n"
     "Thanks,\n[your name]\n\n"
     "Want me to tighten it for a specific recipient or context?"),

    (re.compile(r"los angeles|la weekend|weekend in la", re.I),
     "Three different flavors for an LA weekend:\n\n"
     "1. **Coastal slow.** Saturday morning at El Matador beach in Malibu, lunch at a casual "
     "seafood spot in Topanga, sunset back at the Santa Monica Pier. Sunday — Venice canals walk, "
     "then coffee in Abbot Kinney.\n\n"
     "2. **Art and design.** Saturday at The Broad and MOCA downtown, dinner in Little Tokyo. "
     "Sunday at the Getty Center in the morning (free entry, pay for parking) and a film at the "
     "New Beverly in the evening.\n\n"
     "3. **Hike, taco, repeat.** Sunrise hike up Runyon Canyon, breakfast tacos in Boyle Heights, "
     "afternoon at Griffith Observatory, dinner at a Thai Town spot.\n\n"
     "Want me to optimise around a specific neighborhood or budget?"),

    (re.compile(r"code|programming|javascript|python", re.I),
     "Happy to help with code. SMAC's general assistant is a scripted demo, so I won't actually "
     "run anything — but tell me what you're trying to build and I can sketch the approach. For "
     "real coding workflows, you'd want a proper code-aware assistant."),
     
     (re.compile(r"what is smac|about smac|tell me about smac", re.I),
      "**SMAC** stands for the **Subnational Methane Action Coalition** — a real initiative launched at COP28 that helps subnational governments (states, provinces, regions) reduce methane emissions through expert support, peer learning, and tailored action plans.\n\n"
      "SMAC partners with the **Center for Law, Energy & the Environment (CLEE)** at UC Berkeley, which provides:\n\n"
      "- **Policy & legal frameworks** — helping subnational governments set baselines, build inventories, and design regulations\n"
      "- **Technical assistance** — satellite data, finance opportunities for pilot projects\n"
      "- **Research support** — methane emission reduction strategies tailored to local contexts\n\n"
      "This prototype you're using is a decision-support tool built around SMAC's mission: turning methane emissions data into actionable policy guidance."),

      (re.compile(r"climate trace|climatetrace|who.*climate trace", re.I),
       "**Climate TRACE** (Tracking Real-time Atmospheric Carbon Emissions) is an independent nonprofit that monitors and publishes greenhouse gas emissions worldwide. Founded in 2020 and launched publicly before COP26 in 2021, it has become the largest global inventory of greenhouse gas emission sources.\n\n"
       "**How it works:**\n\n"
       "- Monitors sources like coal mines, power station smokestacks, oil & gas operations\n"
       "- Uses satellite data (from third-party satellites, not their own) and machine learning to estimate emissions\n"
       "- Improves monitoring, reporting, and verification (MRV) for both CO₂ and methane\n"
       "- Releases new data monthly, with about a 2-month lag\n\n"
       "**Why it matters:** Country-level inventories submitted to the UNFCCC are usually delayed by a year or more, and some large emitters don't report at all. Climate TRACE provides a near-real-time, independently verified alternative.\n\n"
       f"Time magazine named it one of the hundred best inventions of 2020. The data this prototype uses (the methane emissions you see across all {len(COUNTRY_ORDER)} countries from {DATA_RANGE_LABEL}) comes from Climate TRACE."),

    (re.compile(r"joke|funny|laugh", re.I),
     "Climate science professor walks into a bar and orders a methane molecule. The bartender "
     "says \"we don't serve gases here.\" The professor says \"you should — they have the highest "
     "warming potential per drink.\"\n\nI'll see myself out."),

    (re.compile(r"thank|thanks|cheers", re.I),
     "You're welcome. If you'd like to dig into the actual data, the Methane Specialist tab on "
     "the left has the full jurisdiction browser wired up."),
]


GENERAL_FALLBACK = (
    "I hear you — I'm a scripted general-purpose chat in this prototype, so my coverage is "
    "shallow outside the methane domain. I can riff on climate basics, draft an email, give "
    "travel ideas, or explain greenhouse gas physics. For your specific question I'd give a "
    "more useful answer if I were a full LLM, but here's my best demo response:\n\n"
    "Try rephrasing toward one of those areas, or jump to the **Methane Specialist** tab on "
    "the left — that side is wired to the real Climate TRACE dataset and will give a "
    "structured answer."
)


def build_general_response(user_text: str) -> str:
    """Returns markdown text for the general assistant."""
    for pattern, reply in GENERAL_PATTERNS:
        if pattern.search(user_text):
            return reply
    return GENERAL_FALLBACK
