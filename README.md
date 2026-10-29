---
title: SMAC Methane Atlas
emoji: 🌫️
colorFrom: green
colorTo: yellow
sdk: streamlit
sdk_version: 1.50.0
app_file: app.py
pinned: false
license: mit
---

# SMAC — Subnational Methane Atlas & Chat

A Streamlit prototype that translates Climate TRACE methane data into structured
policy guidance for subnational governments.

- **11 countries** · **287 subnational units** · **48+ months**, refreshed quarterly
- **Five pages**: Overview, Data & Methods, SMAC (Atlas), Insights, Chat
- **Dual-mode chat**: Methane Specialist + General Assistant, with an A–Z
  jurisdiction picker so you don't need to know the country first
- **Data refresh**: `.github/workflows/refresh-data.yml` pulls the latest
  Climate TRACE country packages on a quarterly cron and redeploys
  automatically — see `scripts/refresh_climatetrace_data.py` for the pipeline
  and its one-time setup checklist.

Source: https://github.com/max177777/smac-methane

## Refreshing the data

All Climate TRACE data is pulled locally, then committed:

    python scripts/fetch_climatetrace_all.py --smac-only   # SMAC pages, ~10 min
    python scripts/fetch_climatetrace_all.py               # + global dataset, several hours

It is resumable (re-run to continue) and writes `data/ct_snapshot.json`, which
sets the snapshot date shown on the site.

The full run also builds `data/global/` (every level-1 admin worldwide) for the
**Global View** page; until those files are committed the page shows a notice.

## Adding a new SMAC member (e.g. Catalonia)

1. Add it to `MEMBER_ROSTER` in `utils/data_loader.py` and in
   `scripts/fetch_point_sources.py` (plus a map pin in `CARBON_MAPPER_LINKS`).
   Until its data is merged, its page shows a "data being added" notice.
2. Run `python scripts/fetch_climatetrace_all.py --smac-only` (resolves its GADM
   id and rebuilds all SMAC files), commit `data/`, push.
   (`scripts/add_jurisdiction.py` still works if you only have a downloaded CSV.)
