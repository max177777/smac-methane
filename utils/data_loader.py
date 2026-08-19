from __future__ import annotations
"""
Data loader for SMAC methane data.
Centralised, cached, the single source of truth for the whole app.

As of the SMAC-2026-DATA-TRACE refresh, this is built on ONE file —
data/SMAC_ch4_summary.csv — a monthly, per-sector-category series for every
actual SMAC member/observer subnational unit. No more separate "monthly" and
"by-sector" files, and no more comprehensive per-country data (every row here
is a real SMAC jurisdiction). Range: 2021-01 through 2026-05.
"""

from pathlib import Path

import pandas as pd
import streamlit as st


DATA_PATH = Path(__file__).parent.parent / "data" / "SMAC_ch4_summary.csv"

# Single source of truth for "what year is the headline stat" and "what range do we
# advertise". 2025 is the latest fully-reported year (2026 only runs through May as of
# this data refresh); update these two when a new year completes.
CURRENT_YEAR = 2025
DATA_RANGE_LABEL = "2021–2026"

# Raw `name` values in the source CSV carry an admin-type suffix ("California State",
# "Beijing Municipality"). Strip it for display; longest match first so e.g. "Union
# Territory" doesn't get partially eaten by a shorter suffix.
_NAME_SUFFIXES = [
    " Autonomous Community", " Union Territory", " Urban Area",
    " Province", " Municipality", " Department", " Region", " State",
]


def _clean_location_name(raw: str) -> str:
    for suf in sorted(_NAME_SUFFIXES, key=len, reverse=True):
        if raw.endswith(suf):
            return raw[: -len(suf)]
    return raw


# Display-only overrides — the underlying data/roster key stays as the left-hand value
# (needed for joins/lookups), but the UI shows the right-hand value instead.
_DISPLAY_NAME_OVERRIDES = {
    "Delhi [New Delhi]": "Delhi",
}


def display_name(location: str) -> str:
    """UI-facing name for a location — use this everywhere a jurisdiction name is
    shown to the user. Does NOT change the underlying key used for data lookups."""
    return _DISPLAY_NAME_OVERRIDES.get(location, location)


# Rows to drop outright: near-duplicate jurisdictions in the source data where two
# overlapping boundaries were both published for the same place. Kept side chosen to
# match earlier confirmed decisions.
_DROP_RAW_NAMES = {"NCT of Delhi Union Territory", "Palembang Urban Area"}


COUNTRY_META = {
    # Africa
    "NGA": {"name": "Nigeria", "region": "Africa", "subunit_type": "state"},
    "ZAF": {"name": "South Africa", "region": "Africa", "subunit_type": "province"},
    # Asia
    "IND": {"name": "India", "region": "Asia", "subunit_type": "state"},
    "KOR": {"name": "South Korea", "region": "Asia", "subunit_type": "province"},
    "IDN": {"name": "Indonesia", "region": "Asia", "subunit_type": "province"},
    "CHN": {"name": "China", "region": "Asia", "subunit_type": "municipality"},
    # Europe
    "DEU": {"name": "Germany", "region": "Europe", "subunit_type": "land"},
    "ESP": {"name": "Spain", "region": "Europe", "subunit_type": "autonomous community"},
    "ITA": {"name": "Italy", "region": "Europe", "subunit_type": "region"},
    # North America
    "CAN": {"name": "Canada", "region": "North America", "subunit_type": "province/territory"},
    "MEX": {"name": "Mexico", "region": "North America", "subunit_type": "state"},
    "USA": {"name": "United States", "region": "North America", "subunit_type": "state"},
    # South America
    "ARG": {"name": "Argentina", "region": "South America", "subunit_type": "province"},
    "BRA": {"name": "Brazil", "region": "South America", "subunit_type": "state"},
    "BOL": {"name": "Bolivia", "region": "South America", "subunit_type": "department"},
}

COUNTRY_ORDER = [
    "NGA", "ZAF",                      # Africa
    "IND", "KOR", "IDN", "CHN",        # Asia
    "DEU", "ESP", "ITA",               # Europe
    "CAN", "MEX", "USA",               # North America
    "ARG", "BRA", "BOL",               # South America
]

# Countries sorted alphabetically by name (for the SMAC page's A-Z-by-country picker).
COUNTRY_ORDER_ALPHA = sorted(COUNTRY_ORDER, key=lambda i: COUNTRY_META[i]["name"])

# A distinct color per country, used to tell countries apart on the SMAC jurisdiction
# picker (15 countries -> 15 hues around the wheel).
COUNTRY_COLORS = {
    "NGA": "#1f9e6b", "ZAF": "#3ca574",
    "IND": "#e07a3f", "KOR": "#c9a227", "IDN": "#8fae2b", "CHN": "#d1495b",
    "DEU": "#3d7ab5", "ESP": "#5c67d1", "ITA": "#8a5cd1",
    "CAN": "#2fa3a3", "MEX": "#e0574c", "USA": "#4c8bf5",
    "ARG": "#c2618d", "BRA": "#3fae7a", "BOL": "#a8763e",
}

# The 8 broad sector categories used in the new dataset, in a fixed display order.
SECTOR_ORDER = [
    "Agriculture", "Waste", "Fossil Fuel Extraction & Mining", "Forestry & Land Use",
    "Manufacturing & Industry", "Power & Heat", "Transportation", "Buildings (Onsite Fuel Use)",
]
SECTOR_COLORS = {
    "Agriculture": "#0e9d6c",
    "Waste": "#eaa93d",
    "Fossil Fuel Extraction & Mining": "#c9645a",
    "Forestry & Land Use": "#4c8bf5",
    "Manufacturing & Industry": "#7c5cbf",
    "Power & Heat": "#2f6fa8",
    "Transportation": "#d97757",
    "Buildings (Onsite Fuel Use)": "#b9c4bd",
}

# Quick-action mitigation bullets per sector category, used to build each jurisdiction's
# Methane Action Plan from its top emission sources. Generic best-practice actions —
# not jurisdiction-specific policy (that lives in policy_content.py).
SECTOR_ACTIONS = {
    "Agriculture": [
        "Support methane-reducing livestock feed additives and improved herd management",
        "Expand manure management systems (anaerobic digesters, covered lagoons)",
        "Promote alternate wetting-and-drying for rice cultivation where applicable",
    ],
    "Waste": [
        "Expand landfill gas capture and flaring/utilization systems",
        "Divert organic waste from landfills via composting or anaerobic digestion",
        "Upgrade wastewater treatment to capture fugitive methane",
    ],
    "Fossil Fuel Extraction & Mining": [
        "Implement leak detection and repair (LDAR) programs at oil & gas facilities",
        "Eliminate routine flaring and venting; require capture at new permits",
        "Electrify pneumatic devices and compressor stations",
    ],
    "Forestry & Land Use": [
        "Address the drivers of land-use conversion (agriculture expansion, fire)",
        "Protect and restore peatlands and wetlands, which are high-methane land types",
        "Fund reforestation and improved fire management programs",
    ],
    "Manufacturing & Industry": [
        "Require leak detection and repair at methane-intensive industrial processes",
        "Adopt best-available techniques (BAT) for chemical and food-processing methane sources",
        "Incentivize process electrification where feasible",
    ],
    "Power & Heat": [
        "Reduce fugitive emissions from gas-fired generation and distribution",
        "Accelerate the transition to renewables to displace gas-fired capacity",
        "Require methane monitoring at thermal power facilities",
    ],
    "Transportation": [
        "Support leak detection on natural-gas vehicle fleets and fueling infrastructure",
        "Accelerate transit and fleet electrification",
        "Tighten methane-slip standards for gas-fueled vehicles",
    ],
    "Buildings (Onsite Fuel Use)": [
        "Support building-gas leak detection and repair programs",
        "Incentivize electrification of heating and cooking",
        "Improve gas-distribution-network leak monitoring",
    ],
}

# NOTE: `location` below matches the CLEANED name (suffix stripped) — see
# _clean_location_name(). status: "member" (full/voting SMAC member) or "observer".
MEMBER_ROSTER: dict[str, list[dict]] = {
    "NGA": [
        {"location": "Cross River", "status": "member"},
        {"location": "Enugu", "status": "member"},
    ],
    "ZAF": [
        {"location": "Gauteng", "status": "member"},
        {"location": "Western Cape", "status": "member"},
    ],
    "IND": [
        {"location": "Delhi [New Delhi]", "status": "member"},
        {"location": "Punjab", "status": "member"},
    ],
    "KOR": [
        {"location": "Chungcheongnam-do", "status": "member"},
        {"location": "Gyeonggi-do", "status": "member"},
    ],
    "IDN": [
        {"location": "Palembang City", "status": "member"},
        {"location": "Jawa Barat", "status": "member"},
    ],
    "CHN": [
        {"location": "Beijing", "status": "observer"},
    ],
    "DEU": [
        {"location": "Baden-Württemberg", "status": "member"},
    ],
    "ESP": [
        {"location": "Andalucía", "status": "member"},
    ],
    "ITA": [
        {"location": "Lombardia", "status": "observer"},
        {"location": "Emilia-Romagna", "status": "observer"},
    ],
    "CAN": [
        {"location": "British Columbia", "status": "member"},
        {"location": "Québec", "status": "observer"},
        {"location": "Alberta", "status": "observer"},
    ],
    "MEX": [
        {"location": "Jalisco", "status": "member"},
        {"location": "Querétaro", "status": "member"},
        {"location": "Yucatán", "status": "member"},
    ],
    "USA": [
        {"location": "California", "status": "member"},
        {"location": "Colorado", "status": "member"},
        {"location": "Maryland", "status": "member"},
    ],
    "ARG": [
        {"location": "Buenos Aires", "status": "member"},
        {"location": "Córdoba", "status": "member"},
        {"location": "Chubut", "status": "member"},
    ],
    "BRA": [
        {"location": "Espírito Santo", "status": "member"},
        {"location": "Goiás", "status": "member"},
        {"location": "Minas Gerais", "status": "member"},
        {"location": "Pernambuco", "status": "member"},
        {"location": "Piauí", "status": "member"},
        {"location": "Rio de Janeiro", "status": "member"},
        {"location": "Rio Grande do Sul", "status": "member"},
        {"location": "Sergipe", "status": "member"},
    ],
    "BOL": [
        {"location": "Santa Cruz", "status": "member"},
    ],
}


def member_status(iso: str, location: str) -> str | None:
    """'member', 'observer', or None if this (country, subnational unit) isn't an
    actual SMAC member/observer."""
    for row in MEMBER_ROSTER.get(iso, []):
        if row["location"] == location:
            return row["status"]
    return None


def total_member_counts() -> tuple[int, int]:
    """(n_full_members, n_observers) across every country in the roster."""
    members = sum(1 for rows in MEMBER_ROSTER.values() for r in rows if r["status"] == "member")
    observers = sum(1 for rows in MEMBER_ROSTER.values() for r in rows if r["status"] == "observer")
    return members, observers


def all_member_locations() -> list[tuple[str, str]]:
    """Every (iso, location) pair in the roster, sorted alphabetically by country
    name, then alphabetically by location name within that country — used for the
    SMAC page's jurisdiction picker."""
    pairs = []
    for iso in COUNTRY_ORDER_ALPHA:
        locs = sorted(r["location"] for r in MEMBER_ROSTER.get(iso, []))
        pairs.extend((iso, loc) for loc in locs)
    return pairs


@st.cache_data(show_spinner=False)
def load_raw() -> pd.DataFrame:
    """Load + clean the raw CSV. Cached at the dataframe level.
    Normalizes column names to the same internal schema the rest of the app expects:
    iso3_country, location (cleaned), sector, year, month, date, total_emission."""
    df = pd.read_csv(DATA_PATH)
    df = df[~df["name"].isin(_DROP_RAW_NAMES)].copy()
    df["location"] = df["name"].map(_clean_location_name)
    df["iso3_country"] = df["iso3"]
    df["sector"] = df["sector_category"]
    df["total_emission"] = df["total_emissions"]
    df["date"] = pd.to_datetime(df["start_time"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df[["iso3_country", "location", "sector", "year", "month", "date", "total_emission"]]


@st.cache_data(show_spinner=False)
def country_yearly(iso: str) -> pd.DataFrame:
    """Yearly totals for a country, summed across all subnational units."""
    df = load_raw()
    sub = df[df["iso3_country"] == iso]
    return (
        sub.groupby("year", as_index=False)["total_emission"]
        .sum()
        .rename(columns={"total_emission": "ch4_tonnes"})
    )


@st.cache_data(show_spinner=False)
def country_monthly(iso: str) -> pd.DataFrame:
    """Monthly totals for a country, summed across subnational units."""
    df = load_raw()
    sub = df[df["iso3_country"] == iso]
    out = (
        sub.groupby(["year", "month", "date"], as_index=False)["total_emission"]
        .sum()
        .rename(columns={"total_emission": "ch4_tonnes"})
    )
    return out.sort_values("date").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def location_yearly(iso: str, location: str) -> pd.DataFrame:
    """Yearly totals for a single subnational unit."""
    df = load_raw()
    sub = df[(df["iso3_country"] == iso) & (df["location"] == location)]
    return (
        sub.groupby("year", as_index=False)["total_emission"]
        .sum()
        .rename(columns={"total_emission": "ch4_tonnes"})
    )


@st.cache_data(show_spinner=False)
def location_monthly(iso: str, location: str) -> pd.DataFrame:
    """Monthly series for a single subnational unit (summed across sectors)."""
    df = load_raw()
    sub = df[(df["iso3_country"] == iso) & (df["location"] == location)]
    out = (
        sub.groupby(["year", "month", "date"], as_index=False)["total_emission"]
        .sum()
        .rename(columns={"total_emission": "ch4_tonnes"})
    )
    return out.sort_values("date").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def location_yearly_ranking(iso: str, year: int = CURRENT_YEAR) -> pd.DataFrame:
    """Subnational ranking for one year, with YoY change vs the prior year.
    Returns an empty (but correctly-shaped) dataframe if the country has no rows
    for that year — a defensive fallback for future new members with no data yet."""
    df = load_raw()
    sub = df[df["iso3_country"] == iso]
    empty_cols = ["location", "ch4_tonnes_year", "share", "yoy_pct"]
    if sub.empty:
        return pd.DataFrame(columns=empty_cols)
    pivot = (
        sub.groupby(["location", "year"], as_index=False)["total_emission"]
        .sum()
        .pivot(index="location", columns="year", values="total_emission")
        .fillna(0)
    )
    if year not in pivot.columns:
        return pd.DataFrame(columns=empty_cols)
    out = pivot.copy()
    out["share"] = out[year] / out[year].sum() * 100
    if (year - 1) in out.columns:
        out["yoy_pct"] = (out[year] - out[year - 1]) / out[year - 1].replace(0, pd.NA) * 100
    else:
        out["yoy_pct"] = pd.NA
    out = out.sort_values(year, ascending=False).reset_index()
    out = out.rename(columns={year: "ch4_tonnes_year"})
    return out


@st.cache_data(show_spinner=False)
def total_months_of_data() -> int:
    """Count of distinct (year, month) pairs in the dataset."""
    df = load_raw()
    return df[["year", "month"]].drop_duplicates().shape[0]


@st.cache_data(show_spinner=False)
def smac_wide_ranking(year: int = CURRENT_YEAR) -> pd.DataFrame:
    """Every SMAC jurisdiction ranked against every OTHER SMAC jurisdiction (not
    just within its own country) for one year — with only 1-8 jurisdictions per
    country, a within-country rank isn't a meaningful comparison; ranking across
    the full ~36-member roster is. Columns: iso3_country, location, ch4_tonnes_year,
    share (of total SMAC CH4), rank (1 = highest emitter)."""
    df = load_raw()
    sub = df[df["year"] == year]
    agg = (
        sub.groupby(["iso3_country", "location"], as_index=False)["total_emission"].sum()
        .rename(columns={"total_emission": "ch4_tonnes_year"})
        .sort_values("ch4_tonnes_year", ascending=False)
        .reset_index(drop=True)
    )
    total = agg["ch4_tonnes_year"].sum()
    agg["share"] = (agg["ch4_tonnes_year"] / total * 100) if total > 0 else 0.0
    agg["rank"] = agg.index + 1
    return agg


@st.cache_data(show_spinner=False)
def all_countries_year_total(year: int = CURRENT_YEAR) -> pd.DataFrame:
    """One row per country, {year} total + locations count."""
    df = load_raw()
    rows = []
    for iso in COUNTRY_ORDER:
        sub = df[(df["iso3_country"] == iso) & (df["year"] == year)]
        total = sub["total_emission"].sum()
        n_loc = sub["location"].nunique()
        meta = COUNTRY_META[iso]
        rows.append({
            "iso3": iso,
            "name": meta["name"],
            "region": meta["region"],
            "subunit_type": meta["subunit_type"],
            "n_locations": n_loc,
            "ch4_year_tonnes": total,
        })
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def list_locations(iso: str) -> list[str]:
    """Sorted list of subnational units for a country, by CURRENT_YEAR total descending."""
    df = load_raw()
    sub = df[(df["iso3_country"] == iso) & (df["year"] == CURRENT_YEAR)]
    ranked = sub.groupby("location")["total_emission"].sum().sort_values(ascending=False)
    return ranked.index.tolist()


@st.cache_data(show_spinner=False)
def list_all_locations_flat() -> pd.DataFrame:
    """
    Every subnational unit across every country, alphabetised by location name.
    Lets someone jump straight to a jurisdiction ("Alberta", "Sao Paulo") without
    picking a country first. `key` disambiguates and `label` is what's shown in the UI.
    """
    df = load_raw()
    sub = df[df["year"] == CURRENT_YEAR]
    grp = sub.groupby(["location", "iso3_country"], as_index=False)["total_emission"].sum()
    grp["country_name"] = grp["iso3_country"].map(lambda i: COUNTRY_META[i]["name"])
    grp["key"] = grp["location"] + "||" + grp["iso3_country"]
    grp["label"] = grp["location"] + "  ·  " + grp["country_name"]
    grp = grp.sort_values("location", key=lambda s: s.str.lower()).reset_index(drop=True)
    return grp[["key", "location", "iso3_country", "country_name", "label"]]


def fmt_int(n: float) -> str:
    if pd.isna(n):
        return "—"
    return f"{int(round(n)):,}"


def fmt_mt(n: float) -> str:
    if pd.isna(n):
        return "—"
    return f"{n / 1e6:.2f}"


def pct_change(now: float, prior: float) -> float:
    if prior == 0 or pd.isna(prior):
        return float("nan")
    return (now - prior) / prior * 100


# ============== SECTOR DATA ==============
# Sector-category detail now lives in the same master file (no separate by-sector CSV
# needed anymore — the new dataset is sector-level from the start).

def has_sector_data() -> bool:
    return DATA_PATH.exists()


@st.cache_data(show_spinner=False)
def location_sectors(iso: str, location: str, year: int = CURRENT_YEAR) -> pd.DataFrame:
    """Sector breakdown for one subnational unit in one year, sorted descending."""
    df = load_raw()
    sub = df[(df["iso3_country"] == iso) & (df["location"] == location) & (df["year"] == year)]
    return (
        sub.groupby("sector", as_index=False)["total_emission"].sum()
        .sort_values("total_emission", ascending=False)
        .reset_index(drop=True)
    )


@st.cache_data(show_spinner=False)
def top_sectors_pareto(iso: str, location: str, year: int = CURRENT_YEAR,
                        threshold: float = 0.80) -> pd.DataFrame:
    """The smallest set of top-ranked sectors whose cumulative share reaches
    `threshold` (default 80%) of that jurisdiction's total emissions for the year —
    i.e. the 'vital few' sectors driving most of the footprint. Always returns at
    least one row (the single largest sector) even if it alone exceeds the threshold."""
    sec = location_sectors(iso, location, year)
    total = sec["total_emission"].sum()
    if total <= 0 or sec.empty:
        return sec.assign(share=[])
    sec = sec.copy()
    sec["share"] = sec["total_emission"] / total
    sec["cum_share"] = sec["share"].cumsum()
    cutoff_idx = sec[sec["cum_share"] >= threshold].index.min()
    if pd.isna(cutoff_idx):
        cutoff_idx = sec.index.max()
    return sec.loc[: cutoff_idx].reset_index(drop=True)


@st.cache_data(show_spinner=False)
def country_sectors(iso: str, year: int = CURRENT_YEAR) -> pd.DataFrame:
    """Sector breakdown for a whole country (summed across its SMAC jurisdictions) in one year."""
    df = load_raw()
    sub = df[(df["iso3_country"] == iso) & (df["year"] == year)]
    return (
        sub.groupby("sector", as_index=False)["total_emission"].sum()
        .sort_values("total_emission", ascending=False)
        .reset_index(drop=True)
    )


@st.cache_data(show_spinner=False)
def sector_yearly_series(iso: str, location: str | None = None) -> pd.DataFrame:
    """Year x sector totals, either for one subnational unit (location given) or the
    whole country (location=None, summed across its SMAC jurisdictions). Used for
    multi-year sector-composition trend charts."""
    df = load_raw()
    sub = df[df["iso3_country"] == iso]
    if location is not None:
        sub = sub[sub["location"] == location]
    return (
        sub.groupby(["year", "sector"], as_index=False)["total_emission"].sum()
        .rename(columns={"total_emission": "ch4_tonnes"})
    )


def action_plan_bullets(top_sectors: pd.DataFrame, max_per_sector: int = 2) -> list[tuple[str, str]]:
    """(sector, bullet) pairs for every sector in `top_sectors`, pulling from
    SECTOR_ACTIONS. Caps bullets per sector so the plan stays scannable."""
    out = []
    for row in top_sectors.itertuples():
        for bullet in SECTOR_ACTIONS.get(row.sector, [])[:max_per_sector]:
            out.append((row.sector, bullet))
    return out


# ============== SUB-SECTOR / "TOP EMITTING SOURCES" DATA ==============
# Climate TRACE's public per-jurisdiction files don't include individual named
# facilities with coordinates for every sector — there's no lat/lon or asset-ID
# column we can rank. What we DO have is a much finer breakdown than the 8 broad
# categories: 68 `original_inventory_sector` sub-sectors (e.g.
# "enteric-fermentation-cattle-operation", "oil-and-gas-production"). We treat each
# sub-sector as one "emitting source" and rank those — the closest faithful proxy
# for "top emitting sources" the underlying data actually supports. Each is tagged
# with its parent broad sector (matches SECTOR_ORDER) for the sector-color tags.
SUBSECTOR_DATA_PATH = Path(__file__).parent.parent / "data" / "SMAC_ch4_subsectors.csv"


def has_subsector_data() -> bool:
    return SUBSECTOR_DATA_PATH.exists()


@st.cache_data(show_spinner=False)
def load_subsector_raw() -> pd.DataFrame:
    df = pd.read_csv(SUBSECTOR_DATA_PATH)
    df["sub_sector_label"] = df["sub_sector"].map(_prettify_subsector)
    return df


def _prettify_subsector(raw: str) -> str:
    """'enteric-fermentation-cattle-operation' -> 'Enteric Fermentation Cattle Operation'"""
    return " ".join(w.capitalize() for w in raw.split("-"))


@st.cache_data(show_spinner=False)
def top_point_sources(iso: str, location: str, year: int = CURRENT_YEAR,
                       top_n: int = 20) -> pd.DataFrame:
    """Top N emitting sources (sub-sectors) for one jurisdiction/year, ranked by
    CH4 emissions descending. Columns: sub_sector, sub_sector_label, sector,
    total_emission, share (of jurisdiction total, %). Also attaches
    `jurisdiction_total` and `top_n_share_pct` (what % of the jurisdiction's total
    CH4 those top N sources represent) as DataFrame attrs."""
    df = load_subsector_raw()
    sub = df[(df["iso3_country"] == iso) & (df["location"] == location) & (df["year"] == year)]
    empty = pd.DataFrame(columns=["sub_sector", "sub_sector_label", "sector", "total_emission", "share"])
    if sub.empty:
        empty.attrs["jurisdiction_total"] = 0.0
        empty.attrs["top_n_share_pct"] = 0.0
        return empty

    agg = (
        sub.groupby(["sub_sector", "sub_sector_label", "sector"], as_index=False)["total_emission"]
        .sum()
        .sort_values("total_emission", ascending=False)
        .reset_index(drop=True)
    )
    jurisdiction_total = agg["total_emission"].sum()
    agg["share"] = (agg["total_emission"] / jurisdiction_total * 100) if jurisdiction_total > 0 else 0.0

    top = agg.head(top_n).copy()
    top.attrs["jurisdiction_total"] = float(jurisdiction_total)
    top.attrs["top_n_share_pct"] = float(top["share"].sum())
    return top
