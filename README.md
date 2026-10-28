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

## Adding a new SMAC member (e.g. Catalonia)

1. Add it to `MEMBER_ROSTER` in `utils/data_loader.py` and in
   `scripts/fetch_point_sources.py` (plus a map pin in `CARBON_MAPPER_LINKS`).
   Until its data is merged, its page shows a "data being added" notice.
2. Download the jurisdiction's Climate TRACE CSV and merge it:
   `python scripts/add_jurisdiction.py --iso ESP --location "Cataluña" <file.csv>`
3. Fetch its named facilities:
   `python scripts/fetch_point_sources.py --only "ESP||Cataluña"`
4. Commit the updated `data/` files and push.
