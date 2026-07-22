"""
Quarterly data refresh for the SMAC Methane Atlas.

What this does
---------------
1. Downloads the latest Climate TRACE "country package" for each of the 11
   SMAC pilot countries (bulk CSV download, no API key needed).
2. Extracts monthly, subnational-level CH4 ("methane") records.
3. Rebuilds the two flat CSVs the app already reads:
     - data/SMAC_methane_monthly.csv   (iso3_country, location, year, month, total_emission)
     - data/SMAC_methane_by_sector.csv (iso3_country, location, sector, year, total_emission)
4. Leaves everything else (policy text, theme, chat engine) untouched.

Why this needs a one-time check before you trust it blindly
-------------------------------------------------------------
Climate TRACE's bulk "Download Packages" section on https://climatetrace.org/data
is rendered client-side, so the exact download URL per country isn't something
I could confirm by fetching the page from here. Before wiring this into the
scheduled GitHub Action:
  1. Go to https://climatetrace.org/data, pick "Country" view, choose one
     pilot country (e.g. USA), and copy the actual download link.
  2. Compare it against COUNTRY_PACKAGE_URL_TEMPLATE below and fix the
     template if the path differs.
  3. Run this script locally once (`python scripts/refresh_climatetrace_data.py
     --dry-run`) and diff the output against the current data/ files before
     letting the Action commit automatically.

Climate TRACE now publishes a new monthly release (with a ~60-day lag), so
running this quarterly comfortably captures 2-3 new months each cycle. If you
want tighter freshness, drop the cron in the GitHub Action to monthly instead.
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).parent.parent / "data"
MONTHLY_OUT = DATA_DIR / "SMAC_methane_monthly.csv"
SECTOR_OUT = DATA_DIR / "SMAC_methane_by_sector.csv"

# ISO3 codes for the 11 pilot countries (must match utils/data_loader.COUNTRY_ORDER)
COUNTRIES = ["USA", "BRA", "CAN", "DEU", "IND", "KOR", "MEX", "NGA", "ZAF", "ARG", "ESP"]

# --- VERIFY THIS TEMPLATE against the real link before relying on the Action ---
# Climate TRACE bulk country packages are published under downloads.climatetrace.org;
# confirm the exact path (may include a version segment) from climatetrace.org/data.
COUNTRY_PACKAGE_URL_TEMPLATE = (
    "https://downloads.climatetrace.org/latest/country_packages/{iso3}.zip"
)

# The sector taxonomy already used in SMAC_methane_by_sector.csv — matches Climate
# TRACE's own top-level sector names, so no renaming should be needed on ingest.
EXPECTED_SECTORS = {
    "agriculture", "waste", "fossil-fuel-operations", "manufacturing",
    "other-energy-use", "transportation", "power", "land-use-change",
    "mineral-extraction",
}


def download_country_package(iso3: str, session: requests.Session) -> pd.DataFrame:
    """Download and unzip one country's package, return its raw source-level CSV."""
    url = COUNTRY_PACKAGE_URL_TEMPLATE.format(iso3=iso3)
    resp = session.get(url, timeout=120)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        # The package contains several CSVs; we want the monthly, source-level,
        # subnational-resolution methane file. Adjust this filter once you've
        # inspected an actual package's file listing.
        candidates = [n for n in zf.namelist() if "monthly" in n.lower() and n.endswith(".csv")]
        if not candidates:
            raise FileNotFoundError(f"No monthly CSV found in {iso3} package: {zf.namelist()}")
        with zf.open(candidates[0]) as f:
            return pd.read_csv(f)


def build_monthly_and_sector_tables(raw_by_country: dict[str, pd.DataFrame]):
    """
    Reshape raw per-country source-level data into the two flat tables the app
    expects. Column names on the left are what Climate TRACE ships; adjust if
    the real package uses different names (check the data guide PDF linked
    from climatetrace.org/data).
    """
    monthly_rows = []
    sector_rows = []

    for iso3, raw in raw_by_country.items():
        gas = raw[raw["gas"].str.lower() == "ch4"].copy()

        monthly = (
            gas.groupby(["subnational_unit", "year", "month"], as_index=False)
            ["emissions_quantity"].sum()
            .rename(columns={
                "subnational_unit": "location",
                "emissions_quantity": "total_emission",
            })
        )
        monthly["iso3_country"] = iso3
        monthly_rows.append(monthly[["iso3_country", "location", "year", "month", "total_emission"]])

        sector = (
            gas.groupby(["subnational_unit", "sector", "year"], as_index=False)
            ["emissions_quantity"].sum()
            .rename(columns={
                "subnational_unit": "location",
                "emissions_quantity": "total_emission",
            })
        )
        sector["iso3_country"] = iso3
        sector_rows.append(sector[["iso3_country", "location", "sector", "year", "total_emission"]])

    return pd.concat(monthly_rows, ignore_index=True), pd.concat(sector_rows, ignore_index=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                         help="Download and reshape, but write to /tmp instead of data/, for inspection.")
    args = parser.parse_args()

    session = requests.Session()
    raw_by_country = {}
    for iso3 in COUNTRIES:
        print(f"Downloading {iso3}...", file=sys.stderr)
        try:
            raw_by_country[iso3] = download_country_package(iso3, session)
        except Exception as e:
            print(f"  FAILED for {iso3}: {e}", file=sys.stderr)
            print("  Check COUNTRY_PACKAGE_URL_TEMPLATE against the real link on "
                  "climatetrace.org/data before re-running.", file=sys.stderr)
            sys.exit(1)

    monthly_df, sector_df = build_monthly_and_sector_tables(raw_by_country)

    # Sanity checks before overwriting anything
    unexpected = set(sector_df["sector"].unique()) - EXPECTED_SECTORS
    if unexpected:
        print(f"WARNING: unexpected sector names found: {unexpected}. "
              f"Check whether the app's sector chart code needs updating.", file=sys.stderr)

    monthly_out = Path("/tmp/SMAC_methane_monthly.csv") if args.dry_run else MONTHLY_OUT
    sector_out = Path("/tmp/SMAC_methane_by_sector.csv") if args.dry_run else SECTOR_OUT

    monthly_df.to_csv(monthly_out, index=False)
    sector_df.to_csv(sector_out, index=False)
    print(f"Wrote {len(monthly_df):,} monthly rows -> {monthly_out}", file=sys.stderr)
    print(f"Wrote {len(sector_df):,} sector rows -> {sector_out}", file=sys.stderr)


if __name__ == "__main__":
    main()
