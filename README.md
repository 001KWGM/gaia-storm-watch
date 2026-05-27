# GAIA Marine Storm Watch v0.5

Public-facing storm event visualiser for general interest and GAIA Marine brand awareness.

This version is configured as a public display dashboard:

- public users register with name and email before viewing;
- public users can view/select curated content only;
- GAIA controls source choices, event window, thresholds, inputs, data processing and updates;
- no public upload or processing controls are exposed;
- weather maps, radar, satellite and synoptic/isobar references are linked to official source pages rather than copied or rehosted;
- official coast cameras are provided as official source links / previews, not archived or rehosted by GAIA Marine.

## v0.6 public-release review notes

This revision is hardened for a public-display workflow. The dashboard is intended as a general-interest storm-event visualiser and brand-awareness demonstrator. It is not official emergency, forecast, marine-safety, operational or commercial decision advice.

Public users can only view/select curated dashboard content. GAIA Marine controls all source choices, thresholds, processing settings, data updates and interpretation boundaries internally.

All maps, graphs, camera references, weather-reference cards, tables and digest text include source/time captions where applicable. Third-party camera imagery, radar products, satellite imagery and weather-map graphics are linked or previewed from official source pages; they are not copied, downloaded, archived or rehosted by GAIA Marine in this prototype.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Deploy to Streamlit Community Cloud

Push the repository to GitHub. In Streamlit Community Cloud deploy:

- Repository: `gaia-storm-watch`
- Branch: `main`
- Main file path: `app.py`

## Registration / lead capture

The registration form writes to Google Sheets when Streamlit secrets are configured. If Google Sheets is not configured, the app falls back to a local CSV at:

```text
data/processed/registrations_local_fallback.csv
```

The local fallback is suitable for local testing only. On Streamlit Community Cloud it should not be treated as durable lead storage.

### Google Sheet setup

Create a Google Sheet named, for example:

```text
GAIA Storm Watch Registrations
```

Create a worksheet named:

```text
Registrations
```

The app will create headers if the sheet is empty.

### Streamlit secrets

Use `.streamlit/secrets_template.toml` as the template. Do not commit real secrets.

In Streamlit Community Cloud:

```text
App > Settings > Secrets
```

Paste the `[registration]` and `[gcp_service_account]` blocks.

Share the Google Sheet with the service-account `client_email` as Editor.

## Weather maps / radar / isobar references

Configured in:

```text
config/weather_references.yaml
```

These are external official source references. The dashboard does not download, reproduce, archive or rehost BOM maps/radar/satellite products in this version.

## Public contact details

Configured in:

```text
config/app_config.yaml
```

Relevant fields:

```yaml
contact_email: info@gaia-marine.com.au
website_url: https://gaia-marine.com.au
```

## Legal / public positioning

This app is a general-interest public-data event visualiser. It is not an official forecast, warning, emergency advice product, marine safety tool, or operational decision-support system.

Official information should be accessed from the relevant official source pages, including Bureau of Meteorology, Emergency WA and WA Department of Transport and Major Infrastructure.
