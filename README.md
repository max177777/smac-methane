---
title: SMAC Methane Inventory Tool
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

Source: https://github.com/max177777/smac-methane-app
