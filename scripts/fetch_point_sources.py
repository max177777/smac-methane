"""
Fetches TRUE point sources — individual named facilities (a specific landfill,
a specific oil & gas site) — from the public Climate TRACE v7 API, and writes
data/SMAC_point_sources.csv for the app to read.

WHY THIS EXISTS
The Top 20 section used to rank *sub-sectors* ("solid-waste-disposal"), because
data/SMAC_ch4_subsectors.csv is aggregated at that level. Ken asked for the top
20 *facilities* so an action plan can name specific sites. /v7/sources returns
exactly that — e.g. "Central Sanitary Landfill", 4,868 t CH4, with coordinates.

HOW IT WORKS (two phases)
  Phase 1 — resolve each SMAC jurisdiction to its GADM id via /v7/admins?name=...
            (Maryland -> USA.21_1). Results are cached to data/smac_gadm_ids.json
            so you can eyeball them and so phase 2 can be re-run without
            re-resolving. Delete that file to force a fresh lookup.
  Phase 2 — page through /v7/sources?gadmId=<that id> per jurisdiction.

  This two-phase shape is necessary because /v7/sources rows carry only
  `country` and coordinates — there is no state/province field to match on,
  so the jurisdiction has to be pinned by querying with its GADM id.

RUN THIS LOCALLY, NOT ON THE SERVER
The app never calls the API at request time — the v7 API is a beta release and
asks users to keep volume low. Run this when you want fresh data, commit the
resulting CSV, deploy. Same pattern as build_subsector_data.py.

    python -m pip install pandas requests
    python scripts/fetch_point_sources.py
"""

from pathlib import Path
import json
import sys
import time

import pandas as pd

try:
    import requests
except ImportError:
    sys.exit("Missing dependency. Run: python -m pip install pandas requests")

BASE_URL = "https://api.climatetrace.org/v7"
OUT_PATH = Path(__file__).parent.parent / "data" / "SMAC_point_sources.csv"
GADM_CACHE = Path(__file__).parent.parent / "data" / "smac_gadm_ids.json"

# Sectors whose sources are discrete, nameable facilities you can act on.
# Deliberately excluded: transportation, forestry/land-use, and most of
# agriculture — there a "source" is a road segment or grid cell, not a site,
# and an unfiltered ranking would be swamped by them. Landfills come via waste.
POINT_SOURCE_SECTORS = [
    "power",
    "fossil-fuel-operations",
    "manufacturing",
    "mineral-extraction",
    "waste",
]

YEAR = 2025          # latest complete year, matches CURRENT_YEAR in data_loader
GAS = "ch4"          # methane specifically — this is a methane tool
PAGE_SIZE = 100      # API max
MAX_ROWS_PER_JURISDICTION = 5000   # CA and Minas Gerais hit the old 1000 cap;
                                   # truncation would silently drop big emitters
                                   # since API order isn't guaranteed by emissions
SLEEP = 0.35         # be polite to a beta API

# Search term to send to /v7/admins when the roster name doesn't find the
# jurisdiction directly. Left side = our roster location name.
# Value may be a single term or a list of candidates tried in order — the
# admins endpoint 404s on some short names (e.g. plain "Delhi").
ADMIN_SEARCH_OVERRIDES = {
    "Delhi [New Delhi]": ["NCT of Delhi", "Delhi [New Delhi]", "New Delhi", "Delhi"],
    "Palembang City": "Palembang",
}


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


def _get(path, params):
    r = requests.get(f"{BASE_URL}/{path}", params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def _as_list(payload):
    """The API has returned bare lists and wrapped objects across releases."""
    if isinstance(payload, dict):
        for key in ("admins", "sources", "data", "results", "assets"):
            if isinstance(payload.get(key), list):
                return payload[key]
        return []
    return payload or []


# ---------------- PHASE 1: resolve GADM ids ----------------

def resolve_gadm_id(iso, location):
    """Look up one jurisdiction's GADM id. Returns (id, matched_name) or (None, None).

    /v7/admins requires one of name/bbox/level, and its name search is fuzzy and
    cross-country (searching "Punjab" also returns Pakistan's), so we filter the
    results down to level_0_id == our ISO3 ourselves.
    """
    terms = ADMIN_SEARCH_OVERRIDES.get(location, location)
    if isinstance(terms, str):
        terms = [terms]

    results, term = [], terms[0]
    for candidate in terms:
        try:
            found = _as_list(_get("admins", {"name": candidate, "limit": 50}))
        except requests.HTTPError as e:
            # the endpoint 404s on some names rather than returning an empty
            # list — that's "no match", not a failure worth aborting on
            if e.response is not None and e.response.status_code == 404:
                continue
            print(f"    ! admins lookup failed for {location}: {type(e).__name__}: {e}")
            return None, None
        except Exception as e:
            print(f"    ! admins lookup failed for {location}: {type(e).__name__}: {e}")
            return None, None
        if any(r.get("level_0_id") == iso for r in found):
            results, term = found, candidate
            break
        time.sleep(SLEEP)

    in_country = [r for r in results if r.get("level_0_id") == iso]
    if not in_country:
        print(f"    ? no admin in {iso} matched any of: {terms}")
        return None, None

    # Prefer level 1 (state/province). Palembang is a city, so fall back to
    # whatever level did match rather than dropping it.
    lvl1 = [r for r in in_country if r.get("level") == 1]
    pool = lvl1 or in_country

    # Prefer a name that starts with what we asked for ("Maryland State" for
    # "Maryland"), over an unrelated substring hit.
    exact = [r for r in pool if r.get("name", "").lower().startswith(term.lower())]
    pick = (exact or pool)[0]
    if len(pool) > 1:
        others = ", ".join(r.get("name", "?") for r in pool[:4] if r is not pick)
        print(f"    note: {len(pool)} candidates for '{term}' in {iso}; "
              f"picked '{pick.get('name')}' (others: {others})")
    return pick.get("id"), pick.get("name")


def build_gadm_map():
    if GADM_CACHE.exists():
        print(f"Using cached GADM ids from {GADM_CACHE.name} "
              f"(delete it to re-resolve)\n")
        return json.loads(GADM_CACHE.read_text(encoding="utf-8"))

    print("Phase 1: resolving GADM ids for each SMAC jurisdiction\n")
    mapping = {}
    for iso, roster in MEMBER_ROSTER.items():
        print(f"{COUNTRY_META[iso]['name']} ({iso})")
        for row in roster:
            loc = row["location"]
            gid, matched = resolve_gadm_id(iso, loc)
            if gid:
                print(f"    {loc:24s} -> {gid}  ({matched})")
                mapping[f"{iso}||{loc}"] = gid
            time.sleep(SLEEP)
    GADM_CACHE.parent.mkdir(parents=True, exist_ok=True)
    GADM_CACHE.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResolved {len(mapping)}/{sum(len(v) for v in MEMBER_ROSTER.values())} "
          f"jurisdictions -> {GADM_CACHE.name}\n")
    return mapping


# ---------------- PHASE 2: fetch facilities ----------------

def fetch_sources(gadm_id):
    """Page through /v7/sources for one jurisdiction."""
    rows, offset = [], 0
    while offset < MAX_ROWS_PER_JURISDICTION:
        try:
            payload = _get("sources", {
                "gadmId": gadm_id, "year": YEAR, "gas": GAS,
                "sectors": ",".join(POINT_SOURCE_SECTORS),
                "limit": PAGE_SIZE, "offset": offset,
            })
        except Exception as e:
            print(f"    ! sources fetch failed at offset {offset}: "
                  f"{type(e).__name__}: {e}")
            break
        page = _as_list(payload)
        if not page:
            break
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        time.sleep(SLEEP)
    return rows


def main():
    gadm_map = build_gadm_map()
    if not gadm_map:
        sys.exit("No GADM ids resolved — cannot fetch facilities.")

    print("Phase 2: fetching facilities\n")
    frames = []
    for iso, roster in MEMBER_ROSTER.items():
        for row in roster:
            loc = row["location"]
            gid = gadm_map.get(f"{iso}||{loc}")
            if not gid:
                continue
            raw = fetch_sources(gid)
            if not raw:
                print(f"  {loc} ({iso}): no facilities returned")
                continue
            df = pd.json_normalize(raw)
            keep = {
                "id": "source_id", "name": "source_name",
                "assetType": "asset_type", "sourceType": "source_type",
                "sector": "sector", "subsector": "sub_sector",
                "emissionsQuantity": "ch4_tonnes",
                "centroid.latitude": "lat", "centroid.longitude": "lon",
            }
            cols = {k: v for k, v in keep.items() if k in df.columns}
            out = df[list(cols)].rename(columns=cols)
            out["iso3_country"] = iso
            out["location"] = loc
            out["gadm_id"] = gid
            out["year"] = YEAR
            frames.append(out)
            n_pt = (df.get("sourceType") == "point-source").sum() if "sourceType" in df else 0
            warn = ("  <-- AT CAP, likely truncated: raise MAX_ROWS_PER_JURISDICTION"
                    if len(raw) >= MAX_ROWS_PER_JURISDICTION else "")
            print(f"  {loc} ({iso}): {len(out)} facilities "
                  f"({n_pt} tagged point-source){warn}")
            time.sleep(SLEEP)

    if not frames:
        sys.exit("\nNo facilities returned for any jurisdiction.")

    result = pd.concat(frames, ignore_index=True)
    result = result.dropna(subset=["ch4_tonnes"])
    result = result.sort_values(
        ["iso3_country", "location", "ch4_tonnes"], ascending=[True, True, False])
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT_PATH, index=False)

    print(f"\nWrote {len(result)} facilities across "
          f"{result['location'].nunique()} jurisdictions -> {OUT_PATH}")
    if "sector" in result:
        print("\nBy sector:")
        print(result["sector"].value_counts().to_string())
    print("\nBiggest single facilities overall:")
    cols = [c for c in ("source_name", "location", "sector", "ch4_tonnes") if c in result]
    print(result.nlargest(10, "ch4_tonnes")[cols].to_string(index=False))


if __name__ == "__main__":
    main()
