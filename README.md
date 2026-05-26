# GAIA Marine Storm Watch v0.1

Educational WA coastal storm event visualiser / public-data demonstrator.

This prototype is deliberately **not** an official warning, forecast, emergency advice product, marine safety tool, or operational decision-support system.

## What this prototype does

- Runs immediately using synthetic demonstration data.
- Allows optional CSV upload for public-source data once source formats are confirmed.
- Shows a WA hub map for Perth, Geraldton, Bunbury and Albany.
- Shows event snapshot cards.
- Shows stacked storm timeline plots: wind/pressure, rainfall, wave conditions, water-level/residual indicator.
- Shows hub comparison charts.
- Shows source transparency and caveats.
- Produces a processed CSV in `data/processed/master_conditions.csv`.

## What this prototype does not do yet

- It does not scrape BOM, Emergency WA, or WA DTMI websites.
- It does not reproduce BOM radar imagery.
- It does not provide official warnings or emergency advice.
- It does not include lead capture yet.
- It does not label residual water level as storm surge unless a validated calculation is added.

## First run on local computer

Open PowerShell or Terminal in this folder and run:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The app should open in your browser.

## First run on Streamlit Community Cloud

1. Create a new private GitHub repository, for example `gaia-storm-watch`.
2. Upload all files from this folder.
3. Go to Streamlit Community Cloud.
4. Connect the GitHub repo.
5. Set the app entrypoint to `app.py`.
6. Deploy.

Streamlit Community Cloud deploys directly from GitHub and updates when you push changes.

## Data upload notes

The uploader is flexible but not magic. It tries to detect common column names:

- timestamp, datetime, date_time, time, date
- hub, location, station, site
- hs, Hm0, significant wave height
- gust, wind gust, wind_gust_kmh
- rain, rainfall, rain_mm
- tide, water level, observed water level
- residual, anomaly, surge

For external publication, build a proper source-specific importer after confirming the actual downloaded CSV headers and metadata.

## Legal / publication notes

Before publishing externally:

- Replace synthetic demonstration data with real uploaded public-source data or clearly label the app as demo-only.
- Check each data source's terms, copyright, attribution and disclaimers.
- Do not state that BOM or WA DTMI data is reproduced with permission unless GAIA has that permission.
- Do not present the dashboard as a warning, safety, navigation, emergency or authority product.
- Link users to BOM and Emergency WA for official information.

## Recommended next upgrade

Add a `data/manual_upload_templates/gaia_storm_watch_upload_template.csv` and source-specific importers once the actual DOT/BOM CSV formats are confirmed.
