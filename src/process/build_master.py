from __future__ import annotations

from datetime import datetime
from pathlib import Path
import math
import sys
import numpy as np
import pandas as pd
import pytz

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.config import load_hubs
from src.utils.paths import PROCESSED_DIR, ARCHIVE_DIR

AWST = pytz.timezone("Australia/Perth")
CANONICAL_COLUMNS = [
    "timestamp_awst", "timestamp_utc", "hub", "display_name", "region", "latitude", "longitude",
    "source_mode", "source_agency", "source_dataset", "source_quality_note",
    "wind_speed_kmh", "wind_gust_kmh", "wind_direction_deg", "rainfall_mm", "air_pressure_hpa", "air_temperature_degC",
    "wave_hs_m", "wave_hmax_m", "wave_tp_s", "wave_direction_deg",
    "water_level_m", "predicted_tide_m", "water_level_residual_m", "datum",
    "data_status", "qa_flag", "qa_comment", "ingested_at_awst"
]

COLUMN_ALIASES = {
    "timestamp_awst": ["timestamp_awst", "timestamp", "datetime", "date_time", "time", "date time", "date"],
    "hub": ["hub", "location", "station", "site"],
    "wind_speed_kmh": ["wind_speed_kmh", "wind kmh", "wind_speed", "wind speed", "wind_spd_kmh"],
    "wind_gust_kmh": ["wind_gust_kmh", "gust_kmh", "wind gust", "gust", "max wind gust"],
    "wind_direction_deg": ["wind_direction_deg", "wind_dir", "wind direction", "wd", "wind_deg"],
    "rainfall_mm": ["rainfall_mm", "rain_mm", "rain", "rainfall", "precip_mm"],
    "air_pressure_hpa": ["air_pressure_hpa", "pressure_hpa", "barometer", "mslp", "pressure"],
    "air_temperature_degC": ["air_temperature_degC", "temperature", "temperature_2m", "air temp", "air temperature", "temp"],
    "wave_hs_m": ["wave_hs_m", "hs", "significant wave height", "h_sig", "hm0", "sig_wave_height"],
    "wave_hmax_m": ["wave_hmax_m", "hmax", "maximum wave height", "max wave height"],
    "wave_tp_s": ["wave_tp_s", "tp", "peak period", "peak_period", "period"],
    "wave_direction_deg": ["wave_direction_deg", "wave_dir", "wave direction", "dp", "direction"],
    "water_level_m": ["water_level_m", "tide_m", "tide", "observed water level", "water level"],
    "predicted_tide_m": ["predicted_tide_m", "predicted_tide", "predicted tide", "prediction"],
    "water_level_residual_m": ["water_level_residual_m", "residual", "tide residual", "surge", "anomaly"],
}


def _canonical_name(raw: str) -> str:
    return str(raw).strip().lower().replace("_", " ")


def _find_column(df: pd.DataFrame, target: str) -> str | None:
    cols = {_canonical_name(c): c for c in df.columns}
    for alias in COLUMN_ALIASES.get(target, []):
        key = _canonical_name(alias)
        if key in cols:
            return cols[key]
    # loose contains pass
    for alias in COLUMN_ALIASES.get(target, []):
        key = _canonical_name(alias)
        for norm, original in cols.items():
            if key in norm:
                return original
    return None


def _coerce_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce")


def _coerce_awst_timestamp(series: pd.Series) -> pd.Series:
    ts = pd.to_datetime(series, errors="coerce", dayfirst=True)
    if getattr(ts.dt, "tz", None) is None:
        return ts.dt.tz_localize("Australia/Perth", nonexistent="NaT", ambiguous="NaT")
    return ts.dt.tz_convert("Australia/Perth")


def _phase_multiplier(t_hours: np.ndarray, peak_offset_hours: float) -> np.ndarray:
    return np.exp(-((t_hours - peak_offset_hours) ** 2) / (2 * 24 ** 2))


def build_demo_master() -> pd.DataFrame:
    cfg = load_hubs()
    hubs = cfg["hubs"]
    # Public demo data must not show future values as if they are observations.
    # Build records only up to the lesser of event end and current AWST time.
    configured_start = pd.Timestamp(cfg["event"]["start_awst"], tz="Australia/Perth")
    configured_end = pd.Timestamp(cfg["event"]["end_awst"], tz="Australia/Perth")
    now_awst = pd.Timestamp.now(tz="Australia/Perth").floor("3h")
    end = min(configured_end, now_awst)
    start = configured_start
    # If the configured event has not started yet, provide a short approach-context
    # dataset ending now so the public prototype still renders without future records.
    if start > end:
        start = end - pd.Timedelta(hours=24)
    idx = pd.date_range(start, end, freq="3h")
    rows = []
    ingested = pd.Timestamp.now(tz="Australia/Perth").strftime("%Y-%m-%d %H:%M:%S %Z")

    hub_offsets = {"Perth": 0, "Geraldton": -9, "Bunbury": 5, "Albany": 16}
    rng = np.random.default_rng(42)
    for hub, meta in hubs.items():
        hours = np.arange(len(idx)) * 3
        storm = _phase_multiplier(hours, 72 + hub_offsets.get(hub, 0))
        secondary = _phase_multiplier(hours, 112 + hub_offsets.get(hub, 0)) * 0.45
        wave = 0.7 + 3.2 * storm + 1.2 * secondary + rng.normal(0, 0.08, len(idx))
        gust = 28 + 76 * storm + 28 * secondary + rng.normal(0, 2.5, len(idx))
        rain = np.maximum(0, 1.5 + 21 * storm + 8 * secondary + rng.normal(0, 2.0, len(idx)))
        pressure = 1015 - 28 * storm - 8 * secondary + rng.normal(0, 0.8, len(idx))
        temp = 22 - 2.5 * storm + rng.normal(0, 0.4, len(idx))
        water = 0.75 + 0.45 * np.sin(np.linspace(0, 14 * math.pi, len(idx))) + 0.32 * storm
        pred = 0.75 + 0.45 * np.sin(np.linspace(0, 14 * math.pi, len(idx)))
        resid = water - pred
        for i, ts in enumerate(idx):
            rows.append({
                "timestamp_awst": ts,
                "timestamp_utc": ts.tz_convert("UTC"),
                "hub": hub,
                "display_name": meta.get("display_name", hub),
                "region": meta.get("region", ""),
                "latitude": meta.get("lat"),
                "longitude": meta.get("lon"),
                "source_mode": "Synthetic demonstration data",
                "source_agency": "GAIA Marine demonstration dataset",
                "source_dataset": "Synthetic event-shaped profile for prototype testing",
                "source_quality_note": "Not observed data. Replace with uploaded public-source data before external publication.",
                "wind_speed_kmh": max(0, gust[i] * 0.62),
                "wind_gust_kmh": max(0, gust[i]),
                "wind_direction_deg": (230 + 35 * np.sin(i / 6)) % 360,
                "rainfall_mm": rain[i],
                "air_pressure_hpa": pressure[i],
                "air_temperature_degC": temp[i],
                "wave_hs_m": max(0, wave[i]),
                "wave_hmax_m": max(0, wave[i] * 1.75),
                "wave_tp_s": 7 + 5 * storm[i] + rng.normal(0, 0.2),
                "wave_direction_deg": (245 + 20 * np.sin(i / 8)) % 360,
                "water_level_m": water[i],
                "predicted_tide_m": pred[i],
                "water_level_residual_m": resid[i],
                "datum": "Demo datum",
                "data_status": "Demo",
                "qa_flag": "Demo data",
                "qa_comment": "Synthetic data for prototype behaviour only.",
                "ingested_at_awst": ingested,
            })
    return pd.DataFrame(rows)[CANONICAL_COLUMNS]


def normalize_uploaded_file(uploaded_file, fallback_hub: str | None = None) -> pd.DataFrame:
    raw = pd.read_csv(uploaded_file)
    out = pd.DataFrame()

    ts_col = _find_column(raw, "timestamp_awst")
    if ts_col is None:
        raise ValueError(f"No timestamp-like column found in {uploaded_file.name}. Expected timestamp/date/time/datetime.")
    out["timestamp_awst"] = _coerce_awst_timestamp(raw[ts_col])
    out["timestamp_utc"] = out["timestamp_awst"].dt.tz_convert("UTC")

    hub_col = _find_column(raw, "hub")
    if hub_col:
        out["hub"] = raw[hub_col].astype(str).str.strip().replace("", fallback_hub or "Uploaded")
    else:
        out["hub"] = fallback_hub or "Uploaded"

    for col in CANONICAL_COLUMNS:
        if col in ["timestamp_awst", "timestamp_utc", "hub"]:
            continue
        src = _find_column(raw, col)
        if src is not None and col not in ["display_name", "region", "source_mode", "source_agency", "source_dataset", "source_quality_note", "datum", "data_status", "qa_flag", "qa_comment", "ingested_at_awst"]:
            out[col] = _coerce_number(raw[src])
        else:
            out[col] = pd.NA

    cfg_hubs = load_hubs()["hubs"]
    for hub, meta in cfg_hubs.items():
        mask = out["hub"].astype(str).str.lower().eq(hub.lower())
        out.loc[mask, "display_name"] = meta.get("display_name", hub)
        out.loc[mask, "region"] = meta.get("region", "")
        out.loc[mask, "latitude"] = meta.get("lat")
        out.loc[mask, "longitude"] = meta.get("lon")

    out["source_mode"] = "Uploaded public-source data"
    out["source_agency"] = "User supplied"
    out["source_dataset"] = getattr(uploaded_file, "name", "uploaded csv")
    out["source_quality_note"] = "Uploaded data are displayed as supplied after column normalisation. Check source metadata before publication."
    out["datum"] = out["datum"].fillna("Not specified")
    out["data_status"] = "Uploaded"
    out["qa_flag"] = "Unverified source"
    out["qa_comment"] = "Column-normalised only; not independently validated."
    out["ingested_at_awst"] = pd.Timestamp.now(tz="Australia/Perth").strftime("%Y-%m-%d %H:%M:%S %Z")

    out = out.dropna(subset=["timestamp_awst"])
    return out[CANONICAL_COLUMNS]


def qa_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for hub, g in df.groupby("hub"):
        rows.append({
            "hub": hub,
            "records": len(g),
            "first_record_awst": g["timestamp_awst"].min(),
            "latest_record_awst": g["timestamp_awst"].max(),
            "source_mode": ", ".join(sorted(set(g["source_mode"].dropna().astype(str))))[:120],
            "missing_wave_records": int(g["wave_hs_m"].isna().sum()),
            "missing_wind_records": int(g["wind_gust_kmh"].isna().sum()),
            "missing_water_level_records": int(g["water_level_m"].isna().sum()),
        })
    return pd.DataFrame(rows)


def save_master(df: pd.DataFrame, filename: str = "master_conditions.csv") -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / filename
    df.to_csv(path, index=False)
    stamp = pd.Timestamp.now(tz="Australia/Perth").strftime("%Y%m%d_%H%M%S")
    archive = ARCHIVE_DIR / f"master_conditions_{stamp}.csv"
    df.to_csv(archive, index=False)
    qa_summary(df).to_csv(PROCESSED_DIR / "source_status.csv", index=False)
    return path


if __name__ == "__main__":
    master = build_demo_master()
    path = save_master(master)
    print(f"Wrote {path}")
