# GAIA Marine Storm Watch v0.2

Educational public-data visualisation for Western Australian coastal storm events.

This app is designed for general interest and GAIA Marine capability demonstration only. It is not an official forecast, warning, emergency advice product, marine safety tool, or operational decision-support system.

## What v0.2 includes

- GAIA Marine branded Streamlit interface.
- Synthetic demonstration data that runs immediately.
- Optional CSV upload and flexible column normalisation.
- Four coastal hubs: Perth, Geraldton, Bunbury and Albany.
- Event snapshot cards.
- WA hub map.
- Event-shape overview.
- Stacked storm timeline charts.
- Hub comparison charts.
- General-interest indicator counts.
- Data coverage heatmap.
- Source transparency tab.
- Downloadable processed CSV.
- Downloadable Markdown event digest.
- Prototype interest form using a pre-filled email link instead of storing personal data.

## Local run

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Or double-click:

```text
run_local.bat
```

## Streamlit Cloud deployment

Main file path:

```text
app.py
```

No secrets are required for this version.

## Updating from v0.1 in GitHub Desktop

1. Copy the contents of this v0.2 folder into your existing local `gaia-storm-watch` repository folder.
2. Allow Windows to replace existing files.
3. Open GitHub Desktop.
4. Confirm changed files appear.
5. Summary: `Upgrade to GAIA Storm Watch v0.2`
6. Click `Commit to main`.
7. Click `Push origin`.
8. Streamlit should redeploy automatically.

## Upload CSV format

The app accepts flexible column names. Best practice is to use this canonical structure:

```text
timestamp_awst,hub,wind_speed_kmh,wind_gust_kmh,wind_direction_deg,rainfall_mm,air_pressure_hpa,wave_hs_m,wave_hmax_m,wave_tp_s,wave_direction_deg,water_level_m,predicted_tide_m,water_level_residual_m
```

Timestamps are interpreted as AWST if no timezone is supplied.

## Publication discipline

Before public release:

- Keep official BOM / Emergency WA links visible.
- Do not describe this as an emergency, warning, safety or operational decision-support tool.
- Do not label water-level residual as storm surge unless independently validated.
- Do not reproduce BOM radar/camera products unless permission and terms are checked.
- Replace synthetic data with checked public-source data and preserve source caveats.

## Legal / source note

Source data remains subject to the relevant agency terms, copyright, disclaimers and conditions of use. GAIA Marine has processed and visualised information independently for general interest and capability demonstration.
