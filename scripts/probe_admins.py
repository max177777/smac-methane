"""
One-off probe: figure out how to look up SUBNATIONAL GADM ids on the
Climate TRACE v7 API.

Why: /v7/sources returns facility rows with `country` and coordinates but NO
admin/state/province field, so we can't assign a facility to a SMAC
jurisdiction by name. The fix is to query /v7/sources with a subnational
gadmId (e.g. Maryland's, not just "USA") — which means first discovering what
those ids are.

    python scripts/probe_admins.py

Prints raw responses. Send the output back and the fetch script gets finalised
against what the API actually returns.
"""

import json

import requests

BASE = "https://api.climatetrace.org/v7"
TIMEOUT = 45


def show(label, url, params=None):
    print("=" * 70)
    print(label)
    print(f"GET {url}  params={params}")
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        print(f"status: {r.status_code}")
        if r.status_code != 200:
            print("body:", r.text[:400])
            return None
        data = r.json()
        if isinstance(data, dict):
            print("top-level keys:", list(data.keys())[:15])
            for k in ("admins", "data", "results", "items"):
                if k in data and isinstance(data[k], list):
                    data = data[k]
                    break
        if isinstance(data, list):
            print(f"list length: {len(data)}")
            if data:
                print("first record:")
                print(json.dumps(data[0], indent=2)[:900])
                if len(data) > 1:
                    print("second record (keys only):", list(data[1].keys()))
        else:
            print("payload:", json.dumps(data, indent=2)[:600])
        return data
    except Exception as e:
        print(f"ERROR {type(e).__name__}: {e}")
        return None
    finally:
        print()


if __name__ == "__main__":
    # 1. does /admins exist at all, and what does a record look like?
    show("1. /admins  (no filters)", f"{BASE}/admins", {"limit": 3})

    # 2. can we filter it down to one country?
    show("2. /admins filtered to USA", f"{BASE}/admins",
         {"countries": "USA", "limit": 5})
    show("2b. /admins  ?country=USA", f"{BASE}/admins",
         {"country": "USA", "limit": 5})

    # 3. is there a name search? (looking for Maryland specifically)
    show("3. /admins name search 'Maryland'", f"{BASE}/admins",
         {"name": "Maryland", "limit": 5})
    show("3b. /admins ?search=Maryland", f"{BASE}/admins",
         {"search": "Maryland", "limit": 5})

    # 4. admin LEVEL filter — level 1 is states/provinces
    show("4. /admins level=1 for USA", f"{BASE}/admins",
         {"country": "USA", "level": 1, "limit": 5})

    # 5. sanity check: does /sources accept a subnational gadmId?
    #    USA.21_1 is GADM's usual id for Maryland — if this returns rows,
    #    the whole approach works and we just need the id list.
    show("5. /sources with subnational gadmId USA.21_1",
         f"{BASE}/sources",
         {"gadmId": "USA.21_1", "year": 2025, "gas": "ch4",
          "sectors": "waste", "limit": 3})

    print("=" * 70)
    print("Done. Send this whole output back.")
