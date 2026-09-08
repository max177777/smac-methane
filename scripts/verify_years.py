"""
Check whether the multi-year point-source fetch actually produced different
data per year, or whether the API ignored the `year` parameter and handed back
the same rows six times.

Every jurisdiction came back with an identical facility count in all six years,
which is suspicious. Counts alone could legitimately be stable (the same plants
exist year to year) — the decisive test is whether the EMISSIONS VALUES differ.

    python scripts/verify_years.py
"""

from pathlib import Path

import pandas as pd

CSV = Path(__file__).parent.parent / "data" / "SMAC_point_sources.csv"

if not CSV.exists():
    raise SystemExit(f"Not found: {CSV}")

df = pd.read_csv(CSV)
print(f"{len(df):,} rows | years: {sorted(df['year'].unique())}\n")

# --- Test 1: does one specific facility's emissions change across years? ---
key = ["source_id"] if "source_id" in df.columns else ["source_name", "location"]
sample_ids = (df.groupby(key)["year"].nunique()
                .sort_values(ascending=False).head(3).index.tolist())

print("=" * 62)
print("TEST 1 — same facility across years (values should DIFFER)")
print("=" * 62)
for sid in sample_ids:
    if not isinstance(sid, tuple):
        sid = (sid,)
    mask = pd.Series(True, index=df.index)
    for col, val in zip(key, sid):
        mask &= df[col] == val
    sub = df[mask].sort_values("year")
    name = sub["source_name"].iloc[0] if "source_name" in sub else str(sid)
    loc = sub["location"].iloc[0] if "location" in sub else ""
    print(f"\n{name}  ({loc})")
    for _, r in sub.iterrows():
        print(f"   {int(r['year'])}: {r['ch4_tonnes']:,.2f} t")
    n_distinct = sub["ch4_tonnes"].round(6).nunique()
    print(f"   -> {n_distinct} distinct value(s) across {len(sub)} years", end="")
    print("   *** ALL IDENTICAL — year param had no effect ***"
          if n_distinct == 1 else "   (varies, looks real)")

# --- Test 2: whole-year totals ---
print("\n" + "=" * 62)
print("TEST 2 — total CH4 per year (should differ year to year)")
print("=" * 62)
totals = df.groupby("year")["ch4_tonnes"].sum()
for yr, v in totals.items():
    print(f"   {int(yr)}: {v:,.2f} t")
if totals.round(2).nunique() == 1:
    print("\n   *** every year has an IDENTICAL total — the API returned the")
    print("       same payload regardless of `year`. The year selector would")
    print("       show the same Top 20 on every year. ***")
else:
    print("\n   totals differ by year — data is genuinely year-specific.")

# --- Test 3: are the facility sets themselves identical? ---
print("\n" + "=" * 62)
print("TEST 3 — facility set per year")
print("=" * 62)
if "source_id" in df.columns:
    sets = {int(y): set(g["source_id"]) for y, g in df.groupby("year")}
    years = sorted(sets)
    base = sets[years[0]]
    same = all(sets[y] == base for y in years[1:])
    print(f"   identical facility IDs in every year: {same}")
    for y in years:
        print(f"   {y}: {len(sets[y]):,} facilities")
