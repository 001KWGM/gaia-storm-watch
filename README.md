# GAIA Marine Storm Watch v0.8

Public-facing WA coastal storm event viewer.

This version is deliberately simplified: one main page, one location selector, one time slider, visible map, selected-time cards, official weather/radar/rainfall/synoptic links, official coast camera links, a simple trend chart, location stats, and source/legal notes.

Public viewers cannot upload data, change thresholds, select APIs, trigger processing, or access internal settings. GAIA Marine controls all inputs, source choices, time windows, parameters and updates internally.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Deploy

Push the repo to GitHub and deploy `app.py` on Streamlit Community Cloud.

## Registration

The registration gate is enabled by default. For durable capture on Streamlit Cloud, configure Google Sheets credentials in Streamlit secrets using `.streamlit/secrets_template.toml` as a guide. Do not commit real secrets to GitHub.

## Legal position

This dashboard is a general-interest visualisation only. It is not official emergency, forecast, marine-safety, operational, commercial-decision or navigation advice. External weather maps, radar, rainfall, warning and camera products are linked to official source pages and are not rehosted by GAIA Marine.
