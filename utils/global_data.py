from __future__ import annotations
"""
Data access for the Global View of Methane page — every level-1 admin
(state / province / region) Climate TRACE covers, not just SMAC members.

Built offline by scripts/fetch_climatetrace_all.py into data/global/:
  admins.csv            gadm_id, name, location, iso3, country_name
  ch4_monthly.csv       gadm_id, year, month, ch4_tonnes
  ch4_sector_year.csv   gadm_id, year, sector (the site's 8 categories), ch4_tonnes
  top_facilities.csv    gadm_id, year, source_name, asset_type, sector, sub_sector,
                        ch4_tonnes, lat, lon  (top 20 per admin-year)

Deliberately lighter than the SMAC pages: totals, trend, sector mix and the
top 20 facilities — no sub-sector drill-down, no policy library. If the files
aren't there yet, has_global_data() is False and the page says so.
"""

import json
import unicodedata
from pathlib import Path

import pandas as pd
import streamlit as st

GLOBAL_DIR = Path(__file__).parent.parent / "data" / "global"
SMAC_GADM_IDS = Path(__file__).parent.parent / "data" / "smac_gadm_ids.json"


def has_global_data() -> bool:
    return (GLOBAL_DIR / "admins.csv").exists() and (GLOBAL_DIR / "ch4_monthly.csv").exists()


def fold(text: str) -> str:
    """'Córdoba' -> 'cordoba' — accent-insensitive search key."""
    return "".join(c for c in unicodedata.normalize("NFKD", str(text))
                   if not unicodedata.combining(c)).lower()


@st.cache_data(show_spinner=False)
def admins() -> pd.DataFrame:
    """One row per admin, with a display label and a folded search alias.
    Columns: gadm_id, name, location, iso3, country_name, label, smac_key."""
    df = pd.read_csv(GLOBAL_DIR / "admins.csv")
    df["country_name"] = df["country_name"].fillna(df["iso3"])
    # Accented names get a plain-ASCII alias so "cordoba" finds Córdoba —
    # the search box is a literal substring match.
    def _label(r):
        base = f'{r["location"]}  ·  {r["country_name"]}'
        plain = fold(r["location"])
        return base if plain == r["location"].lower() else f"{base}  ({plain.title()})"
    df["label"] = df.apply(_label, axis=1)
    df["smac_key"] = df["gadm_id"].map(smac_gadm_map())   # "ISO||Location" if a SMAC member
    return df.sort_values(["location", "country_name"],
                          key=lambda s: s.map(fold)).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def smac_gadm_map() -> dict:
    """gadm_id -> 'ISO||Location' for SMAC members, so the page can point a
    member to its full profile instead of the lighter global view."""
    try:
        m = json.loads(SMAC_GADM_IDS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {gid: key for key, gid in m.items()}


@st.cache_data(show_spinner=False)
def monthly() -> pd.DataFrame:
    df = pd.read_csv(GLOBAL_DIR / "ch4_monthly.csv")
    df["date"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))
    return df


@st.cache_data(show_spinner=False)
def sector_year() -> pd.DataFrame:
    p = GLOBAL_DIR / "ch4_sector_year.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame(
        columns=["gadm_id", "year", "sector", "ch4_tonnes"])


@st.cache_data(show_spinner=False)
def facilities() -> pd.DataFrame:
    p = GLOBAL_DIR / "top_facilities.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


# ------------------------------------------------------------ per-admin views
def admin_monthly(gid: str) -> pd.DataFrame:
    m = monthly()
    return m[m["gadm_id"] == gid].sort_values("date").reset_index(drop=True)


def admin_yearly(gid: str) -> pd.DataFrame:
    return (admin_monthly(gid).groupby("year", as_index=False)["ch4_tonnes"].sum())


def admin_months_in_year(gid: str, year: int) -> list[int]:
    m = admin_monthly(gid)
    return sorted(m.loc[m["year"] == year, "month"].tolist())


def admin_like_for_like(gid: str, year: int) -> dict:
    """Same partial-year logic as the SMAC page: a part-year is compared with
    the same months of the previous year, never a full year."""
    m = admin_monthly(gid)
    months = admin_months_in_year(gid, year)
    cur = float(m.loc[m["year"] == year, "ch4_tonnes"].sum())
    prev = float(m.loc[(m["year"] == year - 1) & m["month"].isin(months), "ch4_tonnes"].sum())
    yoy = (cur - prev) / prev * 100 if prev else float("nan")
    return {"total": cur, "n_months": len(months), "is_partial": 0 < len(months) < 12,
            "yoy_pct": yoy}


def admin_sectors(gid: str, year: int) -> pd.DataFrame:
    s = sector_year()
    out = s[(s["gadm_id"] == gid) & (s["year"] == year) & (s["ch4_tonnes"] > 0)]
    return out.sort_values("ch4_tonnes", ascending=False).reset_index(drop=True)


def admin_sector_trend(gid: str) -> pd.DataFrame:
    s = sector_year()
    return s[(s["gadm_id"] == gid) & (s["ch4_tonnes"] > 0)]


def admin_facilities(gid: str, year: int | None = None) -> tuple[pd.DataFrame, int | None]:
    """Top facilities for the admin. Uses `year` if fetched for it, otherwise the
    latest year available — returns (rows, year_used)."""
    f = facilities()
    if f.empty:
        return f, None
    sub = f[f["gadm_id"] == gid]
    if sub.empty:
        return sub, None
    yrs = sorted(sub["year"].unique())
    use = year if year in yrs else yrs[-1]
    return (sub[sub["year"] == use].sort_values("ch4_tonnes", ascending=False)
            .reset_index(drop=True), int(use))


def facility_years() -> list[int]:
    f = facilities()
    return sorted(int(y) for y in f["year"].unique()) if not f.empty else []


@st.cache_data(show_spinner=False)
def year_ranking(year: int) -> pd.DataFrame:
    """Every admin ranked by that year's CH4. Columns: gadm_id, iso3, ch4_tonnes,
    rank_world, rank_country, n_country."""
    m = monthly()
    tot = m[m["year"] == year].groupby("gadm_id", as_index=False)["ch4_tonnes"].sum()
    tot = tot.merge(admins()[["gadm_id", "iso3"]], on="gadm_id", how="left")
    tot["rank_world"] = tot["ch4_tonnes"].rank(ascending=False, method="min").astype(int)
    tot["rank_country"] = tot.groupby("iso3")["ch4_tonnes"].rank(
        ascending=False, method="min").astype(int)
    tot["n_country"] = tot.groupby("iso3")["gadm_id"].transform("size")
    return tot


def data_years() -> list[int]:
    return sorted(int(y) for y in monthly()["year"].unique())
