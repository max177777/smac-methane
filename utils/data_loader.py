from __future__ import annotations
"""
Data loader for SMAC methane data.
Centralised, cached, the single source of truth for the whole app.
"""

from pathlib import Path

import pandas as pd
import streamlit as st


DATA_PATH = Path(__file__).parent.parent / "data" / "SMAC_methane_monthly.csv"

# Single source of truth for "what year is the headline stat" and "what range do we
# advertise". 2025 is the latest fully-reported year (2026 only runs through May as of
# this data refresh); update these two when a new year completes.
CURRENT_YEAR = 2025
DATA_RANGE_LABEL = "2021–2026"


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

# NOTE: as of the August data refresh, the underlying CSV now only contains actual SMAC
# member/observer jurisdictions per country (not every state/province in the country) —
# see MEMBER_ROSTER below. It also now runs 2021 through May 2026.

# The full SMAC roster by subnational unit. `location` matches the CSV's location string
# exactly. status: "member" (full/voting SMAC member) or "observer".
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
    actual SMAC member/observer — e.g. Lagos shows up in the Climate TRACE data
    because it's a Nigerian state, but only Cross River and Enugu are SMAC members."""
    for row in MEMBER_ROSTER.get(iso, []):
        if row["location"] == location:
            return row["status"]
    return None


def total_member_counts() -> tuple[int, int]:
    """(n_full_members, n_observers) across every country in the roster."""
    members = sum(1 for rows in MEMBER_ROSTER.values() for r in rows if r["status"] == "member")
    observers = sum(1 for rows in MEMBER_ROSTER.values() for r in rows if r["status"] == "observer")
    return members, observers


@st.cache_data(show_spinner=False)
def load_raw() -> pd.DataFrame:
    """Load the raw CSV. Cached at the dataframe level."""
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(
        df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2) + "-01"
    )
    return df


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
    """Monthly series for a single subnational unit."""
    df = load_raw()
    sub = df[(df["iso3_country"] == iso) & (df["location"] == location)]
    return sub[["year", "month", "date", "total_emission"]].rename(
        columns={"total_emission": "ch4_tonnes"}
    ).sort_values("date").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def location_yearly_ranking(iso: str, year: int = CURRENT_YEAR) -> pd.DataFrame:
    """Subnational ranking for one year, with YoY change vs the prior year.
    Returns an empty (but correctly-shaped) dataframe if the country has no rows
    yet — e.g. the newest SMAC members, whose data hasn't been loaded in."""
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
    picking a country first. A handful of names repeat across countries (e.g. two
    "La Rioja"s), so `key` disambiguates and `label` is what's shown in the UI.
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


# ============== SECTOR DATA (from preprocessed reference, CH4 by sector x year) ==============
SECTOR_DATA_PATH = Path(__file__).parent.parent / "data" / "SMAC_methane_by_sector.csv"


def has_sector_data() -> bool:
    """True if the preprocessed sector file is present (lets pages degrade gracefully)."""
    return SECTOR_DATA_PATH.exists()


@st.cache_data(show_spinner=False)
def load_sector_raw() -> pd.DataFrame:
    """Load the compact CH4-by-sector file (iso3_country, location, sector, year, total_emission)."""
    return pd.read_csv(SECTOR_DATA_PATH)


@st.cache_data(show_spinner=False)
def location_sectors(iso: str, location: str, year: int = CURRENT_YEAR) -> pd.DataFrame:
    """Sector breakdown for one subnational unit in one year, sorted descending."""
    df = load_sector_raw()
    sub = df[(df["iso3_country"] == iso) & (df["location"] == location) & (df["year"] == year)]
    return (
        sub.groupby("sector", as_index=False)["total_emission"].sum()
        .sort_values("total_emission", ascending=False)
        .reset_index(drop=True)
    )
