"""
Merge ONE new jurisdiction into the app's two Climate TRACE data files,
without rebuilding everything else:

  data/SMAC_ch4_summary.csv     (monthly x 8 sector categories — what every page reads)
  data/SMAC_ch4_subsectors.csv  (monthly x 68 sub-sectors — Top sources + sector drill-down)

Written for Catalonia, which joined SMAC after the Aug 2026 data pull, but it
works for any new member. Re-running it is safe: existing rows for that
(iso3, location) are replaced, not duplicated.

INPUT
The same per-jurisdiction Climate TRACE CSV that build_subsector_data.py reads
(columns include: name, start_time, gas, original_inventory_sector,
total_emissions). Download it from climatetrace.org for the jurisdiction and
pass its path — several files (e.g. one per sector) are fine.

    python scripts/add_jurisdiction.py --iso ESP --location "Cataluña" path\\to\\catalonia.csv

--location must match the roster key in utils/data_loader.py MEMBER_ROSTER.

SECTOR MAPPING
The summary file's 8 categories are NOT quite the sub-sector file's mapping:
reverse-engineering the existing data shows two sub-sectors are filed
differently there (water-reservoirs -> Forestry & Land Use, other-energy-use ->
Buildings). With those two overrides the sub-sector file reproduces the
summary file exactly (zero difference across all 36 jurisdictions), so the new
jurisdiction's rows are built the same way as everyone else's.
"""

from __future__ import annotations

import argparse
import calendar
import importlib.util
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
SUMMARY = ROOT / "data" / "SMAC_ch4_summary.csv"
SUBSECTORS = ROOT / "data" / "SMAC_ch4_subsectors.csv"

# Reuse the one authoritative sub-sector -> broad-sector table.
_spec = importlib.util.spec_from_file_location(
    "build_subsector_data", Path(__file__).parent / "build_subsector_data.py")
_bsd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bsd)
SUBSECTOR_TO_BROAD = _bsd.SUBSECTOR_TO_BROAD
clean_location_name = _bsd.clean_location_name

SUMMARY_OVERRIDES = {
    "water-reservoirs": "Forestry & Land Use",
    "other-energy-use": "Buildings (Onsite Fuel Use)",
}

SECTOR_ORDER = [
    "Agriculture", "Waste", "Fossil Fuel Extraction & Mining", "Forestry & Land Use",
    "Manufacturing & Industry", "Power & Heat", "Transportation", "Buildings (Onsite Fuel Use)",
]

COUNTRY_NAMES = {
    "NGA": "Nigeria", "ZAF": "South Africa", "IND": "India", "KOR": "South Korea",
    "IDN": "Indonesia", "CHN": "China", "DEU": "Germany", "ESP": "Spain", "ITA": "Italy",
    "CAN": "Canada", "MEX": "Mexico", "USA": "United States", "ARG": "Argentina",
    "BRA": "Brazil", "BOL": "Bolivia",
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("raw", nargs="+", help="Climate TRACE jurisdiction CSV file(s)")
    ap.add_argument("--iso", required=True, help="ISO3 country code, e.g. ESP")
    ap.add_argument("--location", required=True,
                    help='Roster key, e.g. "Cataluña" (must match MEMBER_ROSTER)')
    ap.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    args = ap.parse_args()

    iso, location = args.iso.upper(), args.location
    if iso not in COUNTRY_NAMES:
        sys.exit(f"Unknown ISO3 {iso!r}. Add it to COUNTRY_NAMES (and COUNTRY_META in the app).")

    frames = []
    for p in args.raw:
        df = pd.read_csv(p)
        need = {"name", "start_time", "gas", "original_inventory_sector", "total_emissions"}
        missing = need - set(df.columns)
        if missing:
            sys.exit(f"{p}: missing columns {sorted(missing)} — is this a Climate TRACE "
                     f"jurisdiction CSV? Columns found: {list(df.columns)[:15]}")
        frames.append(df)
    raw = pd.concat(frames, ignore_index=True)
    raw = raw[raw["gas"].str.lower() == "ch4"].copy()
    if raw.empty:
        sys.exit("No CH4 rows in the input.")

    names = raw["name"].unique().tolist()
    if len(names) > 1:
        sys.exit(f"Input mixes several jurisdictions: {names}. Pass one jurisdiction's files.")
    raw_name = names[0]
    if clean_location_name(raw_name) != location:
        print(f"note: raw name {raw_name!r} cleans to {clean_location_name(raw_name)!r}; "
              f"storing it under roster key {location!r}")
        raw_name = location  # no suffix -> load_raw() keeps it as-is

    raw["date"] = pd.to_datetime(raw["start_time"])
    raw["year"] = raw["date"].dt.year
    raw["month"] = raw["date"].dt.month
    raw["sub_sector"] = raw["original_inventory_sector"]

    unmapped = sorted(set(raw["sub_sector"]) - set(SUBSECTOR_TO_BROAD))
    if unmapped:
        sys.exit(f"Unmapped sub-sectors — add them to SUBSECTOR_TO_BROAD in "
                 f"build_subsector_data.py first: {unmapped}")

    # Keep to the window every other jurisdiction covers, so one newer file
    # can't silently stretch the site's date range for a single place.
    summary = pd.read_csv(SUMMARY)
    sdates = pd.to_datetime(summary["start_time"])
    lo, hi = sdates.min(), sdates.max()
    before = len(raw)
    raw = raw[(raw["date"] >= lo) & (raw["date"] <= hi)]
    if len(raw) < before:
        print(f"trimmed {before - len(raw)} rows outside {lo:%Y-%m}..{hi:%Y-%m}")
    months = sorted(set(zip(raw["year"], raw["month"])))
    expected = pd.period_range(lo, hi, freq="M")
    if len(months) != len(expected):
        print(f"WARNING: {len(months)} months of data vs {len(expected)} for everyone else "
              f"({lo:%Y-%m}..{hi:%Y-%m}). Charts will show the gap.")

    # ---- sub-sector rows ----
    raw["sector"] = raw["sub_sector"].map(SUBSECTOR_TO_BROAD)
    sub_new = (
        raw.groupby(["year", "month", "sector", "sub_sector"], as_index=False)["total_emissions"].sum()
        .rename(columns={"total_emissions": "total_emission"})
    )
    sub_new.insert(0, "location", location)
    sub_new.insert(0, "iso3_country", iso)

    # ---- summary rows: every month x all 8 categories, zeros included ----
    raw["sector_category"] = raw["sub_sector"].map(
        lambda s: SUMMARY_OVERRIDES.get(s, SUBSECTOR_TO_BROAD[s]))
    cat = raw.groupby(["year", "month", "sector_category"])["total_emissions"].sum()
    rows = []
    for (y, m) in months:
        last = calendar.monthrange(int(y), int(m))[1]
        for sc in SECTOR_ORDER:
            rows.append({
                "country_name": COUNTRY_NAMES[iso], "iso3": iso, "name": raw_name,
                "start_time": f"{int(y)}-{int(m)}-1", "end_time": f"{int(y)}-{int(m)}-{last}",
                "sector_category": sc,
                "total_emissions": float(cat.get((y, m, sc), 0.0)),
            })
    sum_new = pd.DataFrame(rows)

    # ---- sanity check: both files must agree on the jurisdiction total ----
    t_sub, t_sum = sub_new["total_emission"].sum(), sum_new["total_emissions"].sum()
    if abs(t_sub - t_sum) > 1e-6 * max(t_sub, 1):
        sys.exit(f"Internal mismatch: sub-sector total {t_sub:,.1f} vs summary {t_sum:,.1f}")

    yearly = sum_new.assign(year=pd.to_datetime(sum_new["start_time"]).dt.year) \
                    .groupby("year")["total_emissions"].sum()
    print(f"\n{location} ({iso}) — {len(months)} months, CH4 tonnes per year:")
    for y, v in yearly.items():
        print(f"  {y}: {v:,.0f}")

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return

    # ---- replace any previous rows for this jurisdiction, then append ----
    sclean = summary["name"].map(clean_location_name)
    keep = ~((summary["iso3"] == iso) & (sclean == location))
    replaced = int((~keep).sum())
    pd.concat([summary[keep], sum_new], ignore_index=True).to_csv(SUMMARY, index=False)

    subs = pd.read_csv(SUBSECTORS)
    keep2 = ~((subs["iso3_country"] == iso) & (subs["location"] == location))
    pd.concat([subs[keep2], sub_new], ignore_index=True).to_csv(SUBSECTORS, index=False)

    print(f"\nwrote {len(sum_new)} summary rows"
          f"{f' (replaced {replaced})' if replaced else ''} -> {SUMMARY.name}")
    print(f"wrote {len(sub_new)} sub-sector rows -> {SUBSECTORS.name}")
    print("\nNext: python scripts/fetch_point_sources.py --only "
          f"\"{iso}||{location}\"  (named facilities for the Top 20 table)")


if __name__ == "__main__":
    main()
