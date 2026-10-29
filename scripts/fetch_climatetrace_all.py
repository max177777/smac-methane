"""
One fetcher for ALL Climate TRACE methane data the app uses — run locally,
commit the outputs, deploy. The app itself never calls the API.

Replaces the Aug-2026 snapshot files with one consistent, current release:

  SMAC pages (37 members/observers, incl. Catalonia)
    data/SMAC_ch4_summary.csv       monthly x 8 sector categories
    data/SMAC_ch4_subsectors.csv    monthly x 68 sub-sectors
    data/SMAC_point_sources.csv     every point source, every year
    data/smac_gadm_ids.json         roster -> GADM id
  Global View page (every level-1 admin worldwide, ~3,660)
    data/global/admins.csv          id, name, country
    data/global/ch4_monthly.csv     monthly totals
    data/global/ch4_sector_year.csv yearly x 8 sector categories
    data/global/ch4_subsector_year.csv  yearly x sub-sector (non-zero only)
    data/global/top_facilities.csv  top 20 point sources per admin per year
  data/ct_snapshot.json             pull date + API version (shown on the site)

ENDPOINTS (confirmed by scripts/probe runs, Oct 2026)
  /v7/admins?level=1&limit=&offset=      every level-1 admin (filter by level_0_id ourselves;
                                         the country param is ignored)
  /v7/sources/emissions?gadmId=&gas=ch4&year=YYYY
                                         totals + sectors + sub-sectors, monthly. ONE year per
                                         call — since/to/years params are silently ignored.
  /v7/sources?gadmId=&gas=ch4&year=&sectors=&limit=&offset=
                                         facilities — same 5 sectors as fetch_point_sources.py
                                         (power, fossil-fuel-operations, manufacturing,
                                         mineral-extraction, waste). Unchanged methodology.

USAGE — everything is resumable: re-running skips work already cached.

    python scripts/fetch_climatetrace_all.py --smac-only        # ~10 min: SMAC pages only
    python scripts/fetch_climatetrace_all.py                    # everything (several hours)
    python scripts/fetch_climatetrace_all.py --countries ESP,MEX --limit-admins 5   # quick test
    python scripts/fetch_climatetrace_all.py --build-only       # rebuild outputs from cache

The raw cache lives OUTSIDE the repo (default: ../ct_cache next to the repo
folder) so it can never be committed by accident. Delete it to force a
completely fresh pull.

METHODOLOGY IS UNCHANGED FROM THE AUG-2026 SNAPSHOT
- 8 sector categories: SUBSECTOR_TO_BROAD from build_subsector_data.py, with the
  two overrides the original summary file used (other-energy-use -> Buildings,
  water-reservoirs -> Forestry). Both output files now use that one mapping.
- Facilities: same 5 sectors, same 5000-row cap per jurisdiction-year.
- Delhi: the original data uses the "Delhi [New Delhi] Urban Area" boundary,
  which is not a GADM admin and can't be queried by gadmId (IND.25_1 is the
  smaller NCT of Delhi: ~156k vs ~302k t in 2025). Its summary + sub-sector rows
  are therefore carried over unchanged from the existing files (KEEP_EXISTING),
  and data/ct_snapshot.json records that they come from the earlier snapshot.
"""

from __future__ import annotations

import argparse
import calendar
import importlib.util
import json
import sys
import time
from collections import defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

try:
    import requests
except ImportError:
    sys.exit("Missing dependency. Run: python -m pip install pandas requests")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
GLOBAL = DATA / "global"
BASE = "https://api.climatetrace.org/v7"
API_VERSION = "v7"
YEARS = list(range(2021, 2027))
GAS = "ch4"
SLEEP = 0.25
PAGE = 100
MAX_FACILITY_ROWS = 5000      # per admin-year; CA / Minas Gerais needed > 1000
TOP_N_GLOBAL = 20

# Jurisdictions whose summary/sub-sector rows are copied from the existing files
# instead of the API (see METHODOLOGY above). Value = snapshot those rows are from.
KEEP_EXISTING = {("IND", "Delhi [New Delhi]"): "31 August 2026"}

# Fallback only, for a sub-sector missing from SUBSECTOR_TO_BROAD: Climate TRACE's
# own sector for that row -> the site's 8 categories.
CT_SECTOR_TO_BROAD = {
    "agriculture": "Agriculture",
    "waste": "Waste",
    "fossil-fuel-operations": "Fossil Fuel Extraction & Mining",
    "mineral-extraction": "Fossil Fuel Extraction & Mining",
    "forestry-and-land-use": "Forestry & Land Use",
    "manufacturing": "Manufacturing & Industry",
    "fluorinated-gases": "Manufacturing & Industry",
    "power": "Power & Heat",
    "transportation": "Transportation",
    "buildings": "Buildings (Onsite Fuel Use)",
}
SECTOR_ORDER = [
    "Agriculture", "Waste", "Fossil Fuel Extraction & Mining", "Forestry & Land Use",
    "Manufacturing & Industry", "Power & Heat", "Transportation", "Buildings (Onsite Fuel Use)",
]

# Original sub-sector -> category table (build_subsector_data.py) + the summary file's
# two overrides — exactly what add_jurisdiction.py uses, so all three agree.
_bspec = importlib.util.spec_from_file_location("bsd", Path(__file__).parent / "build_subsector_data.py")
_bsd = importlib.util.module_from_spec(_bspec)
_bspec.loader.exec_module(_bsd)
SUBSECTOR_TO_BROAD = {**_bsd.SUBSECTOR_TO_BROAD,
                      "other-energy-use": "Buildings (Onsite Fuel Use)",
                      "water-reservoirs": "Forestry & Land Use"}
_unmapped_seen: set = set()


def broad(sub: str, ct_sector: str) -> str:
    b = SUBSECTOR_TO_BROAD.get(sub)
    if b:
        return b
    if sub not in _unmapped_seen:
        _unmapped_seen.add(sub)
        print(f"    note: sub-sector {sub!r} not in SUBSECTOR_TO_BROAD — filed by Climate TRACE "
              f"sector {ct_sector!r}", flush=True)
    return CT_SECTOR_TO_BROAD.get(ct_sector, "Manufacturing & Industry")


# Roster + GADM resolution live in fetch_point_sources.py — reuse, don't duplicate.
_spec = importlib.util.spec_from_file_location("fps", Path(__file__).parent / "fetch_point_sources.py")
fps = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fps)
MEMBER_ROSTER = fps.MEMBER_ROSTER
COUNTRY_META = fps.COUNTRY_META
if not any(r["location"] == "Cataluña" for r in MEMBER_ROSTER.get("ESP", [])):
    MEMBER_ROSTER.setdefault("ESP", []).append({"location": "Cataluña", "status": "member"})
    fps.ADMIN_SEARCH_OVERRIDES.setdefault("Cataluña", ["Cataluña"])

_session = requests.Session()
OFFLINE = False   # --build-only: read the cache, never call the API, never write the cache


class FetchFailed(Exception):
    """Network/server failure (not a 404) — the admin is NOT cached, so a re-run retries it."""


def log(*a):
    print(*a, flush=True)


def get(path: str, params: dict | None = None, tries: int = 6):
    """GET with retry/backoff. Returns parsed JSON, or None on 404 (= genuinely no data).
    Raises FetchFailed after repeated network/server errors."""
    last = None
    for attempt in range(tries):
        try:
            r = _session.get(f"{BASE}/{path}", params=params, timeout=90)
            if r.status_code == 404:
                return None
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"HTTP {r.status_code}")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last = e
            time.sleep(min(2 ** attempt * 3, 60))   # 3,6,12,24,48s — rides out 502 blips
    raise FetchFailed(f"{path} {params}: {last}")


def as_list(d):
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        for k in ("admins", "sources", "data", "results", "items"):
            if isinstance(d.get(k), list):
                return d[k]
    return []


def clean_name(raw: str) -> str:
    for suf in sorted(fps_suffixes(), key=len, reverse=True):
        if raw.endswith(suf):
            return raw[: -len(suf)]
    return raw


def fps_suffixes():
    return [" Autonomous Community", " Autonomous City", " Autonomous Region", " Union Territory",
            " Urban Area", " Province", " Municipality", " Department", " Region", " State",
            " District", " Territory", " Prefecture", " Governorate", " County", " Oblast"]


# ------------------------------------------------------------ admins
def load_admins(cache: Path) -> pd.DataFrame:
    f = cache / "admins_level1.json"
    if f.exists():
        rows = json.loads(f.read_text(encoding="utf-8"))
    else:
        log("Listing every level-1 admin …")
        rows, off = [], 0
        while True:
            page = as_list(get("admins", {"level": 1, "limit": 1000, "offset": off}))
            if not page:
                break
            rows.extend(page)
            if len(page) < 1000:
                break
            off += 1000
            time.sleep(SLEEP)
        f.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    cf = cache / "admins_level0.json"
    if cf.exists():
        countries = json.loads(cf.read_text(encoding="utf-8"))
    else:
        countries = as_list(get("admins", {"level": 0, "limit": 1000})) or []
        cf.write_text(json.dumps(countries, ensure_ascii=False), encoding="utf-8")
    cname = {c.get("id"): c.get("name") for c in countries}
    df = pd.DataFrame(rows).drop_duplicates("id")
    df = df.rename(columns={"id": "gadm_id", "level_0_id": "iso3"})
    df["location"] = df["name"].map(clean_name)
    df["country_name"] = df["iso3"].map(lambda i: cname.get(i) or (COUNTRY_META.get(i) or {}).get("name") or i)
    log(f"{len(df):,} level-1 admins across {df['iso3'].nunique()} countries")
    return df[["gadm_id", "name", "location", "iso3", "country_name"]]


# ------------------------------------------------------------ emissions
def fetch_emissions(gadm_id: str, cache: Path) -> dict | None:
    """All years for one admin, cached as compact rows. Returns the cache dict."""
    f = cache / "emissions" / f"{gadm_id}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    if OFFLINE:
        return None
    out = {"gadm_id": gadm_id, "name": None, "totals": [], "rows": [], "subsectors": {}}
    any_data = False
    for y in YEARS:
        d = get("sources/emissions", {"gadmId": gadm_id, "gas": GAS, "year": y})
        time.sleep(SLEEP)
        if not d:
            continue
        any_data = True
        out["name"] = out["name"] or (d.get("location") or {}).get("name")
        for t in (d.get("totals") or {}).get("timeseries") or []:
            if t.get("year") == y:
                out["totals"].append([y, t["month"], float(t.get("emissionsQuantity") or 0)])
        for t in (d.get("subsectors") or {}).get("timeseries") or []:
            if t.get("year") != y:
                continue
            sub, sec = t.get("subsector"), t.get("sector")
            out["subsectors"][sub] = sec            # remember every sub-sector seen, even zero
            v = float(t.get("emissionsQuantity") or 0)
            if v:
                out["rows"].append([y, t["month"], sec, sub, v])
    if not any_data:
        out["empty"] = True
    # The latest year is partial. If the API pads not-yet-reported months with
    # zeros, drop them — otherwise the site would treat 2026 as a full year.
    if out["totals"]:
        ly = max(y for y, _, _ in out["totals"])
        nz = [m for y, m, v in out["totals"] if y == ly and v]
        last = max(nz) if nz else 0
        out["totals"] = [t for t in out["totals"] if t[0] != ly or t[1] <= last]
        out["rows"] = [r for r in out["rows"] if r[0] != ly or r[1] <= last]
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return out


# ------------------------------------------------------------ facilities
def fetch_facilities(gadm_id: str, year: int, cache: Path) -> list:
    f = cache / "facilities_5sectors" / f"{gadm_id}_{year}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    if OFFLINE:
        return []
    rows, off = [], 0
    while off < MAX_FACILITY_ROWS:
        page = as_list(get("sources", {"gadmId": gadm_id, "year": year, "gas": GAS,
                                       "sectors": ",".join(fps.POINT_SOURCE_SECTORS),
                                       "limit": PAGE, "offset": off}))
        time.sleep(SLEEP)
        if not page:
            break
        for s in page:
            c = s.get("centroid") or {}
            rows.append({
                "source_id": s.get("id"), "source_name": s.get("name"),
                "asset_type": s.get("assetType"), "source_type": s.get("sourceType"),
                "sector": s.get("sector"), "sub_sector": s.get("subsector"),
                "ch4_tonnes": s.get("emissionsQuantity"),
                "lat": c.get("latitude"), "lon": c.get("longitude"),
            })
        if len(page) < PAGE:
            break
        off += PAGE
    if off >= MAX_FACILITY_ROWS:
        log(f"    ! {gadm_id} {year}: hit {MAX_FACILITY_ROWS} rows, may be truncated")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(rows, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return rows


# ------------------------------------------------------------ builders
def _month_end(y, m):
    return calendar.monthrange(int(y), int(m))[1]


def build_smac(smac: list[tuple[str, str, str]], cache: Path) -> None:
    """smac: [(iso, roster_location, gadm_id)]"""
    sum_rows, sub_rows, fac_frames = [], [], []
    old_sum = pd.read_csv(DATA / "SMAC_ch4_summary.csv")
    old_sub = pd.read_csv(DATA / "SMAC_ch4_subsectors.csv")
    for iso, loc, gid in smac:
        if (iso, loc) in KEEP_EXISTING:
            keep_s = old_sum[(old_sum["iso3"] == iso) & (old_sum["name"].map(clean_name) == loc)]
            keep_u = old_sub[(old_sub["iso3_country"] == iso) & (old_sub["location"] == loc)]
            if keep_s.empty:
                sys.exit(f"KEEP_EXISTING: no existing rows for {loc} — refusing to drop it.")
            # same numbers; only the category label is re-filed so this jurisdiction's
            # sub-sector file uses the same mapping as everyone else's
            keep_u = keep_u.assign(sector=keep_u["sub_sector"].map(SUBSECTOR_TO_BROAD)
                                   .fillna(keep_u["sector"]))
            sum_rows += keep_s.to_dict("records")
            sub_rows += keep_u.to_dict("records")
            log(f"  {loc:22s} {gid:12s} kept from snapshot {KEEP_EXISTING[(iso, loc)]} "
                f"({len(keep_s):,} rows; boundary not queryable by gadmId)")
        else:
            try:
                e = fetch_emissions(gid, cache)
            except FetchFailed as ex:
                sys.exit(f"\nAPI failure on {loc} ({gid}): {ex}\nNothing written — re-run to retry "
                         f"(already-fetched jurisdictions are cached).")
            if not e or e.get("empty"):
                log(f"  ! no emissions for {loc} ({gid}) — left out")
                continue
            months = sorted({(y, m) for y, m, _ in e["totals"]})
            cat = defaultdict(float)
            sub = defaultdict(float)
            for y, m, sec, sname, v in e["rows"]:
                cat[(y, m, broad(sname, sec))] += v
                sub[(y, m, sname)] += v
            for (y, m) in months:
                for sc in SECTOR_ORDER:
                    sum_rows.append({
                        "country_name": COUNTRY_META[iso]["name"], "iso3": iso,
                        # roster key, no suffix: data_loader cleans names anyway
                        "name": loc,
                        "start_time": f"{y}-{m}-1", "end_time": f"{y}-{m}-{_month_end(y, m)}",
                        "sector_category": sc, "total_emissions": cat.get((y, m, sc), 0.0),
                    })
                for sname, sec in e["subsectors"].items():
                    sub_rows.append({
                        "iso3_country": iso, "location": loc, "year": y, "month": m,
                        "sector": broad(sname, sec),
                        "sub_sector": sname, "total_emission": sub.get((y, m, sname), 0.0),
                    })
            y25 = sum(v for y, _, v in e["totals"] if y == 2025)
            log(f"  {loc:22s} {gid:12s} {len(months)} months, 2025 total {y25:,.0f} t CH4")
        for y in YEARS:
            try:
                rows = fetch_facilities(gid, y, cache)
            except FetchFailed as ex:
                sys.exit(f"\nAPI failure on {loc} facilities {y}: {ex}\nRe-run to retry.")
            if rows:
                df = pd.DataFrame(rows)
                df["iso3_country"], df["location"], df["gadm_id"], df["year"] = iso, loc, gid, y
                fac_frames.append(df)

    if not sum_rows:
        sys.exit("No SMAC data built — nothing written.")
    pd.DataFrame(sum_rows).to_csv(DATA / "SMAC_ch4_summary.csv", index=False)
    pd.DataFrame(sub_rows).to_csv(DATA / "SMAC_ch4_subsectors.csv", index=False)
    if fac_frames:
        fac = pd.concat(fac_frames, ignore_index=True).dropna(subset=["ch4_tonnes"])
        fac = fac.sort_values(["iso3_country", "location", "year", "ch4_tonnes"],
                              ascending=[True, True, True, False])
        fac.to_csv(DATA / "SMAC_point_sources.csv", index=False)
        log(f"SMAC facilities: {len(fac):,} rows, "
            f"{fac['location'].nunique()} jurisdictions, by sector: "
            f"{fac['sector'].value_counts().to_dict()}")
    log(f"wrote SMAC_ch4_summary.csv ({len(sum_rows):,}) and "
        f"SMAC_ch4_subsectors.csv ({len(sub_rows):,})")


def build_global(admins: pd.DataFrame, cache: Path, facility_years: list[int]) -> None:
    GLOBAL.mkdir(parents=True, exist_ok=True)
    monthly, secy, suby, top = [], [], [], []
    kept = []
    for gid in admins["gadm_id"]:
        f = cache / "emissions" / f"{gid}.json"
        if not f.exists():
            continue
        e = json.loads(f.read_text(encoding="utf-8"))
        if e.get("empty"):
            continue
        kept.append(gid)
        for y, m, v in e["totals"]:
            monthly.append((gid, y, m, round(v, 3)))
        sy, ssy = defaultdict(float), defaultdict(float)
        for y, m, sec, s, v in e["rows"]:
            b = broad(s, sec)
            sy[(y, b)] += v
            ssy[(y, b, s)] += v
        secy += [(gid, y, b, round(v, 3)) for (y, b), v in sy.items()]
        suby += [(gid, y, b, s, round(v, 3)) for (y, b, s), v in ssy.items() if v]
        for y in facility_years:
            ff = cache / "facilities_5sectors" / f"{gid}_{y}.json"
            if ff.exists():
                rows = json.loads(ff.read_text(encoding="utf-8"))
                rows = sorted((r for r in rows if r.get("ch4_tonnes")),
                              key=lambda r: r["ch4_tonnes"], reverse=True)[:TOP_N_GLOBAL]
                for r in rows:
                    top.append({"gadm_id": gid, "year": y, **{k: r[k] for k in (
                        "source_name", "asset_type", "sector", "sub_sector",
                        "ch4_tonnes", "lat", "lon")}})
    adm = admins[admins["gadm_id"].isin(kept)]
    adm.to_csv(GLOBAL / "admins.csv", index=False)
    pd.DataFrame(monthly, columns=["gadm_id", "year", "month", "ch4_tonnes"]) \
        .to_csv(GLOBAL / "ch4_monthly.csv", index=False)
    pd.DataFrame(secy, columns=["gadm_id", "year", "sector", "ch4_tonnes"]) \
        .to_csv(GLOBAL / "ch4_sector_year.csv", index=False)
    pd.DataFrame(suby, columns=["gadm_id", "year", "sector", "sub_sector", "ch4_tonnes"]) \
        .to_csv(GLOBAL / "ch4_subsector_year.csv", index=False)
    if top:
        t = pd.DataFrame(top)
        t["ch4_tonnes"] = t["ch4_tonnes"].round(2)
        t.to_csv(GLOBAL / "top_facilities.csv", index=False)
    sizes = {p.name: f"{p.stat().st_size / 1e6:.1f} MB" for p in sorted(GLOBAL.glob("*.csv"))}
    log(f"global: {len(adm):,} admins with data -> {sizes}")


# ------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--smac-only", action="store_true", help="only the 37 SMAC jurisdictions")
    ap.add_argument("--build-only", action="store_true", help="no API calls; rebuild outputs from cache")
    ap.add_argument("--countries", help="limit global fetch to these ISO3 codes, comma-separated")
    ap.add_argument("--limit-admins", type=int, help="global fetch: first N admins only (testing)")
    ap.add_argument("--no-global-facilities", action="store_true",
                    help="skip the (slow) global facility fetch")
    ap.add_argument("--global-facility-years", default="2025",
                    help="years for the global top-20 facilities (default 2025)")
    ap.add_argument("--cache", default=str(ROOT.parent / "ct_cache"),
                    help="raw cache folder (default: ../ct_cache, outside the repo)")
    args = ap.parse_args()
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    if args.build_only:
        global OFFLINE
        OFFLINE = True
    log(f"cache: {cache}")

    # ---- SMAC ----
    gadm_map = fps.build_gadm_map()           # reuses data/smac_gadm_ids.json, resolves Catalonia
    smac = []
    for iso, roster in MEMBER_ROSTER.items():
        for r in roster:
            gid = gadm_map.get(f"{iso}||{r['location']}")
            if gid:
                smac.append((iso, r["location"], gid))
            else:
                log(f"  ! no GADM id for {r['location']} ({iso})")
    log(f"\nSMAC: {len(smac)} jurisdictions")
    build_smac(smac, cache)

    if not args.smac_only:
        admins = load_admins(cache)
        if args.countries:
            want = {c.strip().upper() for c in args.countries.split(",")}
            admins = admins[admins["iso3"].isin(want)]
        if args.limit_admins:
            admins = admins.head(args.limit_admins)
        fy = [int(y) for y in args.global_facility_years.split(",") if y.strip()]
        n = len(admins)
        log(f"\nGLOBAL: {n:,} admins")
        t0 = time.time()
        failed = []
        for i, gid in enumerate(admins["gadm_id"], 1):
            try:
                fetch_emissions(gid, cache)
                if not args.no_global_facilities:
                    for y in fy:
                        fetch_facilities(gid, y, cache)
            except FetchFailed as e:
                failed.append(gid)
                log(f"  ! {gid}: {e} — will retry on the next run")
            if i % 25 == 0 or i == n:
                el = time.time() - t0
                log(f"  {i:,}/{n:,}  {el / 60:.0f} min elapsed, "
                    f"~{el / i * (n - i) / 60:.0f} min left")
        if failed:
            log(f"\n{len(failed)} admin(s) failed and were not cached: {failed[:20]} — "
                f"just re-run the same command to retry them.")
        build_global(admins, cache, fy)

    (DATA / "ct_snapshot.json").write_text(json.dumps({
        "pulled": date.today().isoformat(), "api_version": API_VERSION,
        "source": "Climate TRACE /v7/sources/emissions + /v7/sources",
        "kept_from_earlier_snapshot": {f"{i}||{l}": d for (i, l), d in KEEP_EXISTING.items()},
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    log("\nwrote data/ct_snapshot.json — done.")


if __name__ == "__main__":
    main()
