"""
Overview / landing page. All visible text comes from i18n/<lang>.json via t().
"""

import streamlit as st

from utils.theme import inject_theme, eyebrow, dot_logo, dark_band, render_footer
from utils.data_loader import (
    COUNTRY_META, COUNTRY_ORDER, all_countries_year_total, CURRENT_YEAR, DATA_RANGE_LABEL,
    MEMBER_ROSTER, total_member_counts, total_months_of_data, load_subsector_raw,
    country_monthly, country_yearly, fmt_mt, pct_change, display_name,
)
from utils.charts import sparkline_plotly, jurisdiction_map_plotly
from utils.i18n import t, country_name, region_name, subunit_name


inject_theme()

_n_roster = sum(len(v) for v in MEMBER_ROSTER.values())

# ============== HERO ==============
col1, col2 = st.columns([1.4, 1], gap="large")

with col1:
    dot_logo(36)
    eyebrow(t("overview.eyebrow"))
    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;margin:-4px 0 18px;flex-wrap:wrap;">'
        f'<span class="smac-meta" style="font-size:12px;">SMAC · {DATA_RANGE_LABEL}</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"<h1 style='margin-bottom:0;'>{t('overview.hero_title')}</h1>",
                unsafe_allow_html=True)
    st.markdown(
        '<p style="font-family:Inter,sans-serif;font-size:18px;line-height:1.6;'
        'color:var(--ink-soft);max-width:520px;margin-top:24px;font-weight:400;">'
        f"{t('overview.hero_body', n=_n_roster, c=len(COUNTRY_ORDER))}</p>",
        unsafe_allow_html=True,
    )

    st.write("")
    cta1, cta2, cta3 = st.columns([1, 1, 1])
    with cta1:
        if st.button(t("overview.cta_chat"), use_container_width=True, type="primary"):
            st.switch_page("pages/4_Chat.py")
    with cta2:
        if st.button(t("overview.cta_smac"), use_container_width=True, type="secondary"):
            st.switch_page("pages/2_Country_Profile.py")
    with cta3:
        if st.button(t("overview.cta_methods"), use_container_width=True, type="secondary"):
            st.switch_page("pages/5_Data_Methods.py")
    st.markdown(
        f'<div class="smac-meta" style="font-size:10px;margin-top:10px;">{t("overview.new_here")}</div>',
        unsafe_allow_html=True,
    )

with col2:
    summary = all_countries_year_total(CURRENT_YEAR)
    # Roster count, not "jurisdictions with data rows": a member whose figures
    # are still being merged in (e.g. Catalonia) is still a member.
    total_loc = _n_roster
    n_months = total_months_of_data()
    n_subsectors = load_subsector_raw()["sub_sector"].nunique()

    eyebrow(t("overview.glance"))

    def _stat(value, unit, caption, last=False):
        bb = "border-bottom:1px solid var(--line);" if last else ""
        return (
            f'<div style="border-top:1px solid var(--line);{bb}padding:20px 0;display:flex;'
            f'justify-content:space-between;align-items:baseline;gap:12px;">'
            f'<div style="font-family:Quicksand,sans-serif;font-size:42px;font-weight:300;'
            f'letter-spacing:-0.02em;line-height:1;">{value}<span style="font-family:Quicksand,'
            f'sans-serif;font-size:11px;color:var(--ink-soft);margin-left:6px;letter-spacing:0.1em;">'
            f'{unit}</span></div>'
            f'<div style="font-family:Quicksand,sans-serif;font-size:10px;text-transform:uppercase;'
            f'letter-spacing:0.1em;color:var(--ink-soft);text-align:right;max-width:220px;'
            f'line-height:1.4;">{caption}</div></div>'
        )

    st.markdown(
        _stat(len(COUNTRY_ORDER), t("overview.stat_countries"), t("overview.stat_countries_cap"))
        + _stat(total_loc, t("overview.stat_juris"), t("overview.stat_juris_cap"))
        + _stat(n_months, t("overview.stat_months"), t("overview.stat_months_cap"))
        + _stat(n_subsectors, t("overview.stat_sources"), t("overview.stat_sources_cap"), last=True),
        unsafe_allow_html=True,
    )

st.markdown("---")

# ============== HOW TO USE THIS TOOL (page guide) ==============
# CalEPA feedback: first-time visitors couldn't tell what each page was for.
# One card per page — what it shows, the question it answers, and a button.
eyebrow(t("overview.guide_eyebrow"))
st.markdown(f"<h2 style='font-size:2.2rem;margin-bottom:8px;'>{t('overview.guide_title')}</h2>",
            unsafe_allow_html=True)
st.markdown(
    '<p style="font-size:15px;line-height:1.65;color:var(--ink-soft);max-width:720px;'
    f'margin-bottom:22px;">{t("overview.guide_intro")}</p>',
    unsafe_allow_html=True,
)

GUIDE = [
    ("smac", "pages/2_Country_Profile.py"),
    ("global", "pages/8_Global_View.py"),
    ("compare", "pages/3_Comparison.py"),
    ("chat", "pages/4_Chat.py"),
    ("methods", "pages/5_Data_Methods.py"),
    ("faq", "pages/7_FAQ.py"),
    ("contact", "pages/6_Contact.py"),
]
GUIDE_PER_ROW = 3
for row_start in range(0, len(GUIDE), GUIDE_PER_ROW):
    gcols = st.columns(GUIDE_PER_ROW, gap="medium")
    for j, (gk, page) in enumerate(GUIDE[row_start:row_start + GUIDE_PER_ROW]):
        title = t(f"nav.{gk}")
        with gcols[j]:
            st.markdown(
                f'<div class="smac-card" style="padding:20px 22px;min-height:230px;">'
                f'<div style="font-family:Quicksand,sans-serif;font-size:10px;letter-spacing:0.12em;'
                f'color:var(--ink-soft);margin-bottom:8px;">{row_start + j + 1:02d}</div>'
                f'<div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:18px;'
                f'margin-bottom:8px;">{title}</div>'
                f'<div style="font-size:13px;line-height:1.55;color:var(--ink-soft);'
                f'margin-bottom:12px;">{t(f"overview.guide_{gk}_desc")}</div>'
                f'<div style="font-size:12px;line-height:1.45;color:var(--mint-deep);'
                f'font-style:italic;">&ldquo;{t(f"overview.guide_{gk}_q")}&rdquo;</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button(t("overview.guide_open", page=title), key=f"guide_{page}",
                         use_container_width=True):
                st.switch_page(page)
    st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)

st.markdown("---")

# ============== ABOUT SMAC (mirrors smacmethane.org) ==============
smac_l, smac_r = st.columns([1.3, 1], gap="large")

with smac_l:
    eyebrow(t("common.smac_full"))
    st.markdown(f"<h2 style='font-size:2.2rem;'>{t('overview.about_title')}</h2>",
                unsafe_allow_html=True)
    st.markdown(
        '<p style="font-family:Inter,sans-serif;font-size:16px;line-height:1.65;'
        f'color:var(--ink-soft);max-width:640px;margin-bottom:18px;">{t("overview.about_body")}</p>',
        unsafe_allow_html=True,
    )

    smac_btns = st.columns([1, 1, 4])
    with smac_btns[0]:
        st.markdown(
            '<a href="https://www.smacmethane.org/benefits" target="_blank" style="text-decoration:none;">'
            '<span class="smac-pill" style="display:block;text-align:center;padding:10px 22px;font-size:15px;">'
            f'{t("overview.benefits")}</span></a>',
            unsafe_allow_html=True,
        )
    with smac_btns[1]:
        if st.button(t("overview.join"), key="smac_join_btn", type="primary"):
            st.switch_page("pages/6_Contact.py")

    st.markdown(
        '<div style="margin-top:16px;margin-bottom:26px;">'
        '<a href="https://www.smacmethane.org/s/SMAC_Letter-from-California_2025-1-yg86.pdf" target="_blank" '
        'style="font-family:Quicksand,sans-serif;font-size:13px;font-weight:700;color:var(--mint-deep);text-decoration:none;">'
        f'\U0001F4C4 {t("overview.ca_letter")} →</a></div>',
        unsafe_allow_html=True,
    )

    eyebrow(t("overview.imperative"))
    st.markdown(
        '<p style="font-family:Inter,sans-serif;font-size:15px;line-height:1.7;'
        f'color:var(--ink-soft);max-width:680px;margin-bottom:14px;">{t("overview.imperative_p1")}</p>'
        '<p style="font-family:Inter,sans-serif;font-size:15px;line-height:1.7;'
        f'color:var(--ink-soft);max-width:680px;margin-bottom:8px;">{t("overview.imperative_p2")}</p>',
        unsafe_allow_html=True,
    )

with smac_r:
    st.markdown('<div style="height:48px;"></div>', unsafe_allow_html=True)
    st.plotly_chart(
        jurisdiction_map_plotly(height=500, show_legend=False),
        use_container_width=True,
        config={"displayModeBar": False},
    )

st.markdown(
    '<div style="border-top:1px solid var(--line);border-bottom:1px solid var(--line);'
    'padding:18px 0;margin:18px 0;display:flex;gap:48px;flex-wrap:wrap;">'
    '<div><div style="font-family:Quicksand,sans-serif;font-size:28px;font-weight:700;">375M+</div>'
    f'<div class="smac-meta" style="font-size:11px;">{t("overview.population")}</div></div>'
    '<div><div style="font-family:Quicksand,sans-serif;font-size:28px;font-weight:700;">US$4.6T+</div>'
    f'<div class="smac-meta" style="font-size:11px;">{t("overview.gdp")}</div></div>'
    '</div>',
    unsafe_allow_html=True,
)

with dark_band():
    eyebrow(t("overview.does_eyebrow"))
    st.markdown(f"<h2 style='font-size:2.2rem;margin-bottom:8px;'>{t('overview.does_title')}</h2>",
                unsafe_allow_html=True)
    st.markdown(
        '<p style="font-family:Inter,sans-serif;font-size:15px;line-height:1.65;'
        f'color:rgba(255,255,255,0.75);max-width:680px;margin-bottom:28px;">{t("overview.does_body")}</p>',
        unsafe_allow_html=True,
    )
    func_cols = st.columns(2)
    for i in range(5):
        with func_cols[i % 2]:
            st.markdown(
                f'<div style="display:flex;gap:12px;margin-bottom:22px;align-items:flex-start;">'
                f'<span style="width:9px;height:9px;border-radius:50%;background:var(--mint);flex-shrink:0;margin-top:7px;"></span>'
                f'<div><div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:15px;color:#ffffff;margin-bottom:4px;">'
                f'{t(f"overview.fn{i + 1}_title")}</div>'
                f'<div style="font-size:13px;line-height:1.55;color:rgba(255,255,255,0.72);">'
                f'{t(f"overview.fn{i + 1}_desc")}</div></div></div>',
                unsafe_allow_html=True,
            )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ============== MEMBERS ==============
n_members, n_observers = total_member_counts()
eyebrow(t("overview.members_eyebrow"))
# Mint emphasis stays on members (not observers) — matches the actual hierarchy.
st.markdown(
    f"<h2 style='font-size:2.2rem;margin-bottom:12px;'>"
    f"{t('overview.members_title', m=n_members, o=n_observers, c=len(COUNTRY_ORDER))}</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    '<p style="font-size:14px;line-height:1.7;color:var(--ink-soft);max-width:720px;'
    f'margin-bottom:26px;">{t("overview.members_body")}</p>',
    unsafe_allow_html=True,
)

REGION_GROUPS = [
    ["Africa", "Asia"],
    ["Europe", "North America"],
    ["South America"],
]
region_to_isos: dict[str, list[str]] = {}
for _iso in COUNTRY_ORDER:
    region_to_isos.setdefault(COUNTRY_META[_iso]["region"], []).append(_iso)

member_cols = st.columns(3, gap="large")
for col, regions in zip(member_cols, REGION_GROUPS):
    with col:
        for region in regions:
            st.markdown(
                f'<div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:15px;'
                f'margin:4px 0 10px;">{region_name(region)}</div>',
                unsafe_allow_html=True,
            )
            for iso in region_to_isos.get(region, []):
                for row in MEMBER_ROSTER.get(iso, []):
                    tag = (f"  <span style='color:var(--ink-soft);'>({t('common.observer')})</span>"
                           if row["status"] == "observer" else "")
                    st.markdown(
                        f'<div style="font-size:13.5px;line-height:1.9;color:var(--ink);">'
                        f'{display_name(row["location"])}, {country_name(iso)}{tag}</div>',
                        unsafe_allow_html=True,
                    )
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

with dark_band():
    eyebrow(t("overview.method_eyebrow"))
    st.markdown(f"<h2 style='font-size:2.2rem;margin-bottom:32px;'>{t('overview.method_title')}</h2>",
                unsafe_allow_html=True)

    flow_cols = st.columns(5)
    for i in range(5):
        with flow_cols[i]:
            is_last = i == 4
            bg = "var(--mint)" if is_last else "rgba(255,255,255,0.06)"
            text_color = "var(--ink)" if is_last else "#ffffff"
            soft_color = "var(--ink)" if is_last else "rgba(255,255,255,0.65)"
            border_color = "transparent" if is_last else "rgba(255,255,255,0.14)"
            st.markdown(
                f"""
                <div style="padding:24px 18px;background:{bg};border:1px solid {border_color};border-radius:14px;height:100%;color:{text_color};">
                  <div style="font-family:Quicksand,sans-serif;font-weight:700;font-size:11px;color:{soft_color};letter-spacing:0.1em;margin-bottom:10px;">{i + 1:02d} / {t(f"overview.step{i + 1}_tag")}</div>
                  <div style="font-family:Quicksand,sans-serif;font-size:22px;font-weight:700;letter-spacing:-0.01em;margin-bottom:6px;">{t(f"overview.step{i + 1}_title")}</div>
                  <div style="font-size:12.5px;line-height:1.5;color:{soft_color};">{t(f"overview.step{i + 1}_desc")}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ============== COUNTRY GRID ==============
eyebrow(t("overview.grid_eyebrow"))
st.markdown(
    f"<h2 style='font-size:2.2rem;margin-bottom:32px;'>{t('overview.grid_title', c=len(COUNTRY_ORDER))}</h2>",
    unsafe_allow_html=True,
)

cols_per_row = 3
year_totals = all_countries_year_total(CURRENT_YEAR)
for row_start in range(0, len(COUNTRY_ORDER), cols_per_row):
    cols = st.columns(cols_per_row, gap="small")
    for j, iso in enumerate(COUNTRY_ORDER[row_start:row_start + cols_per_row]):
        with cols[j]:
            meta = COUNTRY_META[iso]

            yearly = country_yearly(iso)
            y_prior = float(yearly[yearly["year"] == CURRENT_YEAR - 1]["ch4_tonnes"].iloc[0]) if (CURRENT_YEAR - 1) in yearly["year"].values else 0
            y_now = float(yearly[yearly["year"] == CURRENT_YEAR]["ch4_tonnes"].iloc[0]) if CURRENT_YEAR in yearly["year"].values else 0
            yoy = pct_change(y_now, y_prior)
            n_loc = int(year_totals.query(f"iso3 == '{iso}'")["n_locations"].iloc[0])
            arrow = "↑" if yoy > 0.5 else ("↓" if yoy < -0.5 else "→")
            arrow_color = "var(--warn)" if yoy > 0.5 else ("var(--good)" if yoy < -0.5 else "var(--ink-soft)")
            units = t("overview.n_smac_units", n=n_loc, unit=subunit_name(meta["subunit_type"], n_loc))

            st.markdown(
                f"""
                <div style="border:1px solid var(--line);padding:24px 22px;background:var(--paper);height:100%;">
                  <div style="font-family:Quicksand,sans-serif;font-size:10px;color:var(--ink-soft);letter-spacing:0.16em;display:flex;justify-content:space-between;margin-bottom:14px;">
                    <span>{region_name(meta['region']).upper()}</span><span>ISO · {iso}</span>
                  </div>
                  <div style="font-family:Quicksand,sans-serif;font-size:30px;font-weight:400;letter-spacing:-0.02em;line-height:1;margin-bottom:4px;">{country_name(iso)}</div>
                  <div style="font-family:Inter,sans-serif;font-size:12px;color:var(--ink-soft);margin-bottom:18px;">{units}</div>
                  <div style="display:flex;flex-direction:column;gap:6px;margin-bottom:14px;">
                    <div style="display:flex;justify-content:space-between;border-bottom:1px dotted var(--line-soft);padding-bottom:5px;font-size:12px;">
                      <span style="color:var(--ink-soft);font-family:Quicksand,sans-serif;font-size:10px;letter-spacing:0.08em;text-transform:uppercase;">{t("overview.year_total", y=CURRENT_YEAR)}</span>
                      <span style="font-family:Quicksand,sans-serif;font-weight:500;">{fmt_mt(y_now)} Mt CH₄</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;border-bottom:1px dotted var(--line-soft);padding-bottom:5px;font-size:12px;">
                      <span style="color:var(--ink-soft);font-family:Quicksand,sans-serif;font-size:10px;letter-spacing:0.08em;text-transform:uppercase;">{t("common.yoy")} {str(CURRENT_YEAR - 1)[2:]}→{str(CURRENT_YEAR)[2:]}</span>
                      <span style="font-family:Quicksand,sans-serif;font-weight:500;color:{arrow_color};">{arrow} {yoy:+.2f}%</span>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            monthly = country_monthly(iso)
            st.plotly_chart(sparkline_plotly(monthly, height=50), use_container_width=True,
                            config={"displayModeBar": False}, key=f"spark_{iso}")

render_footer()
