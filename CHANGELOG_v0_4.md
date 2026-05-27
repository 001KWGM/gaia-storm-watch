# GAIA Storm Watch v0.4 changelog

## Public-display hardening

- Converted app from prototype tool into public viewing dashboard.
- Removed public sidebar controls.
- Removed public data-mode selector.
- Removed public CSV upload.
- Removed public source/processing controls.
- Removed processed CSV download.
- Added GAIA-controlled app configuration in `config/app_config.yaml`.
- Limited public interaction to curated viewing selections: hub, metric and camera region.
- Retained prepared public digest download only, controlled by config.
- Clarified that all thresholds, inputs, processing settings and data source choices are controlled internally by GAIA Marine.

## Legal / positioning

- Strengthened general-interest wording.
- Reconfirmed not an emergency, forecast, marine-safety or operational decision-support tool.
- Coast cameras remain official links / page previews only; images are not scraped, downloaded, archived or rehosted.

## Technical

- Kept optional Open-Meteo weather context as an internal server-side setting.
- Removed app-side archive writing during public viewing.
- Confirmed Python syntax compile passes.
- Confirmed demo master build process works.
