from __future__ import annotations
"""
Scripted chat response builder.
Two modes:
  - 'methane'  : structured 5-block response grounded in real data
  - 'general'  : conversational free-form scripted response
"""

import re
from dataclasses import dataclass

from utils.data_loader import (
    COUNTRY_META, country_yearly, country_monthly, location_monthly,
    location_yearly_ranking, fmt_int, pct_change,
)
from utils.policy_content import POLICY, PATHWAYS, GWP100, GWP20


@dataclass
class MethaneContext:
    iso: str
    location: str  # "__all__" or specific name
    metric: str    # "ch4" | "gwp100" | "gwp20"
    output: str    # "data" | "trend" | "policy" | "pathway" | "method"


@dataclass
class ChatBlock:
    """A single block of a structured response."""
    label: str
    content: str  # markdown
    is_method: bool = False


@dataclass
class MethaneResponse:
    blocks: list[ChatBlock]
    chart_df = None  # filled by builder
    chart_subject: str = ""


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
    t = user_text.lower()
    if re.search(r"gwp|co2e|co₂e|warming pot", t):
        return "method"
    if re.search(r"polic|regulat|rule|law|legislation", t):
        return "policy"
    if re.search(r"mitigat|reduce|pathway|abat|action", t):
        return "pathway"
    if re.search(r"trend|over time|grow|increas|decreas|monthly|seasonal", t):
        return "trend"
    return current_output


# ============================================================
# METHANE SPECIALIST RESPONSE
# ============================================================
def build_methane_response(user_text: str, ctx: MethaneContext) -> MethaneResponse:
    mode = _detect_mode_from_text(user_text, ctx.output)
    mult, unit, metric_label = _metric_factor(ctx.metric)
    iso = ctx.iso
    meta = COUNTRY_META[iso]
    country_name = meta["name"]
    subunit_type = meta["subunit_type"]

    # Pick the data slice
    is_loc = ctx.location != "__all__"
    if is_loc:
        monthly = location_monthly(iso, ctx.location)
        yearly = monthly.groupby("year", as_index=False)["ch4_tonnes"].sum()
        subject = ctx.location
    else:
        monthly = country_monthly(iso)
        yearly = country_yearly(iso)
        subject = country_name

    # Yearly aggregates
    def y(year):
        row = yearly[yearly["year"] == year]
        return float(row["ch4_tonnes"].iloc[0]) if len(row) else 0.0

    y21, y22, y23, y24 = y(2021), y(2022), y(2023), y(2024)
    yoy = pct_change(y24, y23)
    drift = pct_change(y24, y21)

    # Subnational ranking for context
    rank = location_yearly_ranking(iso, year=2024)
    total = rank["ch4_tonnes_year"].sum()
    top3_names = rank["location"].head(3).tolist()
    top3_share = rank.head(3)["share"].sum()

    blocks: list[ChatBlock] = []

    # ---------- DATA ----------
    if mode == "data":
        if is_loc:
            share_of_nation = y24 / total * 100 if total else 0
            summary = (
                f"In 2024, **{subject}** emitted **{fmt_int(y24 * mult)} {unit}** "
                f"of methane (under the *{metric_label}* framing). That is "
                f"**{share_of_nation:.2f}%** of {country_name}'s national CH₄ total."
            )
            insight = (
                f"- 2021 baseline: **{fmt_int(y21 * mult)} {unit}**\n"
                f"- 2023: **{fmt_int(y23 * mult)} {unit}**\n"
                f"- 2024: **{fmt_int(y24 * mult)} {unit}**\n"
                f"- Year-over-year: **{yoy:+.2f}%** ({'rising' if yoy > 0 else 'falling'})\n"
                f"- Four-year drift: **{drift:+.2f}%**"
            )
        else:
            summary = (
                f"In 2024, **{country_name}** emitted **{fmt_int(y24 * mult)} {unit}** "
                f"of methane. The top three subnational units "
                f"({', '.join(top3_names)}) together explain **{top3_share:.1f}%** "
                f"of the national footprint."
            )
            top5 = rank.head(5)
            insight = "Top subnational units (2024 CH₄, tonnes):\n\n" + "\n".join(
                f"- **{r.location}** — {fmt_int(r.ch4_tonnes_year)} t ({r.share:.1f}%)"
                for r in top5.itertuples()
            )

        blocks.append(ChatBlock("Summary", summary))
        blocks.append(ChatBlock("Key Data Insight", insight))
        blocks.append(ChatBlock("Policy Context", POLICY[iso]["summary"]))
        path = PATHWAYS.get(iso, [])
        if path:
            actions = " · ".join(f"*{a}*" for a in path[0]["actions"][:3])
            blocks.append(ChatBlock(
                "Recommended Mitigation Pathway",
                f"Sequence by abatement density. Highest-density action set in **{path[0]['sector']}**: {actions}."
            ))
        blocks.append(ChatBlock(
            "Method · Uncertainty",
            f"Data: Climate TRACE 2024 release · monthly subnational methane · 48-month series. "
            f"Metric framing: {metric_label} (multiplier ×{mult:g}). Uncertainty band ≈ ±15-25% at subunit level.",
            is_method=True
        ))

    # ---------- TREND ----------
    elif mode == "trend":
        peak_idx = monthly["ch4_tonnes"].idxmax()
        trough_idx = monthly["ch4_tonnes"].idxmin()
        peak = monthly.loc[peak_idx]
        trough = monthly.loc[trough_idx]
        month_name = lambda m: ["", "January", "February", "March", "April", "May", "June",
                                "July", "August", "September", "October", "November", "December"][int(m)]

        summary = (
            f"Across 2021–2024, **{subject}** shows a **{'rising' if drift > 0 else 'falling'}** "
            f"trajectory of **{drift:+.2f}%** in CH₄. The most recent year-on-year change is "
            f"**{yoy:+.2f}%**."
        )
        insight = (
            f"- Peak month: **{month_name(peak['month'])} {int(peak['year'])}** — "
            f"{fmt_int(peak['ch4_tonnes'])} t CH₄\n"
            f"- Low month: **{month_name(trough['month'])} {int(trough['year'])}** — "
            f"{fmt_int(trough['ch4_tonnes'])} t CH₄\n"
            f"- Range ratio (peak/trough): **{peak['ch4_tonnes'] / trough['ch4_tonnes']:.2f}×**\n"
            f"- Annual average drift: **{drift / 3:+.2f}% / year**"
        )
        if drift > 0:
            policy_ctx = ("A rising trajectory means current policy is not bending the curve. "
                          "Subnational instruments may need binding targets, not voluntary measures.")
        else:
            policy_ctx = ("A falling trajectory does not mean the job is done — sustained "
                          "reduction requires verification, not self-reporting.")

        blocks.append(ChatBlock("Summary", summary))
        blocks.append(ChatBlock("Key Data Insight", insight))
        blocks.append(ChatBlock("Policy Context", policy_ctx))
        path = PATHWAYS.get(iso, [])
        if path:
            blocks.append(ChatBlock(
                "Recommended Mitigation Pathway",
                " · ".join(f"*{a}*" for a in path[0]["actions"])
            ))
        blocks.append(ChatBlock(
            "Method · Uncertainty",
            "Trend computed on raw Climate TRACE monthly aggregates. Seasonality not "
            "deseasonalised in this view; underlying signal is the inter-annual change.",
            is_method=True,
        ))

    # ---------- POLICY ----------
    elif mode == "policy":
        p = POLICY[iso]
        blocks.append(ChatBlock(
            "Summary",
            f"{country_name}'s methane policy stack combines federal mandates with "
            f"subnational implementation. Coverage is uneven — strongest in the dominant sector, "
            f"thinner in agricultural and waste streams."
        ))
        top3_total = rank.head(3)["ch4_tonnes_year"].sum()
        blocks.append(ChatBlock(
            "Key Data Insight",
            f"In 2024, **{', '.join(top3_names)}** together produced "
            f"**{fmt_int(top3_total)} t CH₄** — about **{top3_share:.1f}%** of national methane. "
            f"Yet only a subset of {subunit_type}s have binding instruments beyond the federal floor."
        ))
        policy_text = "\n\n".join(f"**{n}.** {d}" for n, d in p["policies"])
        blocks.append(ChatBlock("Policy Context", policy_text))
        path = PATHWAYS.get(iso, [])
        if path:
            actions = " · ".join(f"*{a}*" for a in path[0]["actions"])
            blocks.append(ChatBlock(
                "Recommended Mitigation Pathway",
                f"Priority gap: align {subunit_type} rules to the dominant emitter. {actions}."
            ))
        blocks.append(ChatBlock(
            "Method · Uncertainty",
            f"Policy text retrieved from official registers. Anti-greenwashing flag: "
            f"{path[0]['flag'] if path else '—'}.",
            is_method=True,
        ))

    # ---------- PATHWAY ----------
    elif mode == "pathway":
        path = PATHWAYS.get(iso, [])
        if not path:
            blocks.append(ChatBlock("Summary", f"No pathway data for {country_name} in this prototype."))
        else:
            blocks.append(ChatBlock(
                "Summary",
                f"Mitigation pathway for {subject} is sequenced by abatement density: "
                f"tackle **{path[0]['sector']}** first (highest tonnes-per-dollar), "
                f"then **{path[1]['sector']}**, then **{path[2]['sector']}**."
            ))
            insight = "Sector-by-sector pathway:\n\n" + "\n".join(
                f"- **{x['sector']}.** {' · '.join(x['actions'])}"
                for x in path
            )
            blocks.append(ChatBlock("Key Data Insight", insight))
            blocks.append(ChatBlock(
                "Policy Context",
                f"Each pathway must clear a greenwashing audit before it counts toward national "
                f"pledges. {POLICY[iso]['summary']}"
            ))
            blocks.append(ChatBlock(
                "Recommended Mitigation Pathway",
                f"Highest-priority near-term action: **{path[0]['actions'][0]}** in the "
                f"{path[0]['sector']} sector. Pair with verification (satellite, third-party audit) "
                f"to preserve credibility."
            ))
            flags = " / ".join(x["flag"] for x in path)
            blocks.append(ChatBlock(
                "Method · Uncertainty",
                f"Pathway logic uses IEA Methane Tracker abatement curves + IPCC AR6 WG3 Ch.6 "
                f"(energy) and Ch.7 (AFOLU). Greenwashing checks: {flags}.",
                is_method=True,
            ))

    # ---------- METHOD ----------
    else:  # method
        blocks.append(ChatBlock(
            "Summary",
            "Methane (CH₄) is short-lived but extremely potent. Converting CH₄ to CO₂-equivalent "
            "depends on the time horizon — that choice changes which sectors look most urgent."
        ))
        insight = (
            f"For {subject}'s {fmt_int(y24)} t CH₄ in 2024:\n\n"
            f"- **GWP100 (×{GWP100}):** ≈ {fmt_int(y24 * GWP100)} t CO₂e — comparable to long-term "
            f"climate accounting.\n"
            f"- **GWP20 (×{GWP20}):** ≈ {fmt_int(y24 * GWP20)} t CO₂e — reflects near-term warming "
            f"pressure relevant to 1.5°C pathways.\n\n"
            f"The GWP20 framing roughly **triples** methane's apparent weight versus GWP100."
        )
        blocks.append(ChatBlock("Key Data Insight", insight))
        blocks.append(ChatBlock(
            "Policy Context",
            "Most national inventories report under GWP100 (UNFCCC convention). Subnational "
            "decision-making is increasingly using GWP20 to justify near-term methane action — "
            "but switching framings without disclosure is itself a greenwashing risk."
        ))
        blocks.append(ChatBlock(
            "Recommended Mitigation Pathway",
            "Report both GWP100 and GWP20 side-by-side. Prioritise fast-mitigation, low-cost "
            "sources (oil & gas leaks, landfill gas) where GWP20 framing materially changes the "
            "cost-benefit."
        ))
        blocks.append(ChatBlock(
            "Method · Uncertainty",
            f"IPCC AR6 WG1 Ch.7 Table 7.15 · GWP100 = 27.2 (non-fossil CH₄), GWP20 = 79.7. "
            f"Values rounded for display. SMAC always discloses which GWP horizon is in use to "
            f"prevent metric-switching greenwashing.",
            is_method=True,
        ))

    response = MethaneResponse(blocks=blocks, chart_subject=subject)
    response.chart_df = monthly
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
       "Time magazine named it one of the hundred best inventions of 2020. The data this prototype uses (the methane emissions you see across all 11 countries from 2021 to 2024) comes from Climate TRACE."),

    (re.compile(r"joke|funny|laugh", re.I),
     "Climate science professor walks into a bar and orders a methane molecule. The bartender "
     "says \"we don't serve gases here.\" The professor says \"you should — they have the highest "
     "warming potential per drink.\"\n\nI'll see myself out."),

    (re.compile(r"thank|thanks|cheers", re.I),
     "You're welcome. If you'd like to dig into the actual data, the Methane Specialist tab on "
     "the left has the full atlas wired up."),
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
