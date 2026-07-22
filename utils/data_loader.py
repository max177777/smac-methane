from __future__ import annotations
"""
Data loader for SMAC methane data.
Centralised, cached, the single source of truth for the whole app.
"""

from pathlib import Path

import pandas as pd
import streamlit as st


DATA_PATH = Path(__file__).parent.parent / "data" / "SMAC_methane_monthly.csv"


COUNTRY_META = {
    "USA": {"name": "United States", "region": "North America", "subunit_type": "state"},
    "BRA": {"name": "Brazil", "region": "South America", "subunit_type": "state"},
    "CAN": {"name": "Canada", "region": "North America", "subunit_type": "province/territory"},
    "DEU": {"name": "Germany", "region": "Europe", "subunit_type": "land"},
    "IND": {"name": "India", "region": "Asia", "subunit_type": "state"},
    "KOR": {"name": "South Korea", "region": "Asia", "subunit_type": "province"},
    "MEX": {"name": "Mexico", "region": "North America", "subunit_type": "state"},
    "NGA": {"name": "Nigeria", "region": "Africa", "subunit_type": "state"},
    "ZAF": {"name": "South Africa", "region": "Africa", "subunit_type": "province"},
    "ARG": {"name": "Argentina", "region": "South America", "subunit_type": "province"},
    "ESP": {"name": "Spain", "region": "Europe", "subunit_type": "autonomous community"},
}

COUNTRY_ORDER = ["USA", "BRA", "CAN", "DEU", "IND", "KOR", "MEX", "NGA", "ZAF", "ARG", "ESP"]


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
def location_monthly(iso: str, location: str) -> pd.DataFrame:
    """Monthly series for a single subnational unit."""
    df = load_raw()
    sub = df[(df["iso3_country"] == iso) & (df["location"] == location)]
    return sub[["year", "month", "date", "total_emission"]].rename(
        columns={"total_emission": "ch4_tonnes"}
    ).sort_values("date").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def location_yearly_ranking(iso: str, year: int = 2024) -> pd.DataFrame:
    """Subnational ranking for one year, with YoY change vs the prior year."""
    df = load_raw()
    sub = df[df["iso3_country"] == iso]
    pivot = (
        sub.groupby(["location", "year"], as_index=False)["total_emission"]
        .sum()
        .pivot(index="location", columns="year", values="total_emission")
        .fillna(0)
    )
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
def all_countries_2024_total() -> pd.DataFrame:
    """One row per country, 2024 total + locations count."""
    df = load_raw()
    rows = []
    for iso in COUNTRY_ORDER:
        sub = df[(df["iso3_country"] == iso) & (df["year"] == 2024)]
        total = sub["total_emission"].sum()
        n_loc = sub["location"].nunique()
        meta = COUNTRY_META[iso]
        rows.append({
            "iso3": iso,
            "name": meta["name"],
            "region": meta["region"],
            "subunit_type": meta["subunit_type"],
            "n_locations": n_loc,
            "ch4_2024_tonnes": total,
        })
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def list_locations(iso: str) -> list[str]:
    """Sorted list of subnational units for a country, by 2024 total descending."""
    df = load_raw()
    sub = df[(df["iso3_country"] == iso) & (df["year"] == 2024)]
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
    sub = df[df["year"] == 2024]
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
def location_sectors(iso: str, location: str, year: int = 2024) -> pd.DataFrame:
    """Sector breakdown for one subnational unit in one year, sorted descending."""
    df = load_sector_raw()
    sub = df[(df["iso3_country"] == iso) & (df["location"] == location) & (df["year"] == year)]
    return (
        sub.groupby("sector", as_index=False)["total_emission"].sum()
        .sort_values("total_emission", ascending=False)
        .reset_index(drop=True)
    )
