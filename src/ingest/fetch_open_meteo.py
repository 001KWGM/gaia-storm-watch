from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import pandas as pd
import requests

OPEN_METEO_ENDPOINT = "https://api.open-meteo.com/v1/forecast"
HOURLY_FIELDS = [
    "temperature_2m",
    "precipitation",
    "pressure_msl",
    "wind_speed_10m",
    "wind_gusts_10m",
    "wind_direction_10m",
]

@dataclass
class FetchResult:
    data: pd.DataFrame
    errors: list[str]


def fetch_hub_weather(hub: str, lat: float, lon: float, timeout: int = 20) -> pd.DataFrame:
    """Fetch hourly weather model context for one hub from Open-Meteo.

    This is used as general-interest weather context only. It is not official
    warning information and should not be labelled as BOM observations.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(HOURLY_FIELDS),
        "timezone": "Australia/Perth",
        "forecast_days": 10,
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }
    r = requests.get(OPEN_METEO_ENDPOINT, params=params, timeout=timeout)
    r.raise_for_status()
    payload = r.json()
    hourly = payload.get("hourly") or {}
    if not hourly or "time" not in hourly:
        raise ValueError("Open-Meteo response did not include hourly time series")
    df = pd.DataFrame(hourly)
    df["timestamp_awst"] = pd.to_datetime(df["time"], errors="coerce").dt.tz_localize("Australia/Perth", nonexistent="NaT", ambiguous="NaT")
    df = df.dropna(subset=["timestamp_awst"])
    out = pd.DataFrame({
        "timestamp_awst": df["timestamp_awst"],
        "hub": hub,
        "air_temperature_degC": pd.to_numeric(df.get("temperature_2m"), errors="coerce"),
        "rainfall_mm": pd.to_numeric(df.get("precipitation"), errors="coerce"),
        "air_pressure_hpa": pd.to_numeric(df.get("pressure_msl"), errors="coerce"),
        "wind_speed_kmh": pd.to_numeric(df.get("wind_speed_10m"), errors="coerce"),
        "wind_gust_kmh": pd.to_numeric(df.get("wind_gusts_10m"), errors="coerce"),
        "wind_direction_deg": pd.to_numeric(df.get("wind_direction_10m"), errors="coerce"),
    })
    return out


def fetch_weather_for_hubs(hubs: dict) -> FetchResult:
    frames: list[pd.DataFrame] = []
    errors: list[str] = []
    for hub, meta in hubs.items():
        try:
            frames.append(fetch_hub_weather(hub, float(meta["lat"]), float(meta["lon"])))
        except Exception as exc:
            errors.append(f"{hub}: {exc}")
    if not frames:
        return FetchResult(pd.DataFrame(), errors)
    return FetchResult(pd.concat(frames, ignore_index=True), errors)


def blend_weather_into_master(master: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    """Merge weather context into the existing master table using nearest-time matching.

    Demo marine/water-level fields are retained. Weather fields are replaced by
    Open-Meteo output where available. Matching tolerance is 90 minutes.
    """
    if master.empty or weather.empty:
        return master
    out_frames = []
    for hub, g in master.groupby("hub"):
        w = weather[weather["hub"] == hub].copy()
        if w.empty:
            out_frames.append(g)
            continue
        left = g.sort_values("timestamp_awst").copy()
        right = w.sort_values("timestamp_awst").copy()
        merged = pd.merge_asof(
            left,
            right,
            on="timestamp_awst",
            by="hub",
            direction="nearest",
            tolerance=pd.Timedelta("90min"),
            suffixes=("", "_auto_weather"),
        )
        for col in ["air_temperature_degC", "rainfall_mm", "air_pressure_hpa", "wind_speed_kmh", "wind_gust_kmh", "wind_direction_deg"]:
            src = f"{col}_auto_weather"
            if src in merged.columns:
                merged[col] = merged[src].combine_first(merged[col])
                merged = merged.drop(columns=[src])
        merged["source_mode"] = "Auto weather context + demo marine context"
        merged["source_agency"] = "Open-Meteo weather model API; GAIA synthetic marine context"
        merged["source_dataset"] = "Open-Meteo forecast weather fields blended with GAIA demonstration marine fields"
        merged["source_quality_note"] = "Weather values are model/API context for general-interest visualisation; wave and water-level fields remain synthetic unless replaced with checked public-source files."
        merged["data_status"] = "Auto weather / demo marine"
        merged["qa_flag"] = "Mixed source context"
        merged["qa_comment"] = "Weather model context blended with synthetic event-shaped marine fields. Not official warning or observed marine-safety data."
        out_frames.append(merged)
    result = pd.concat(out_frames, ignore_index=True)
    drop_cols = [c for c in result.columns if c.endswith("_auto_weather")]
    if drop_cols:
        result = result.drop(columns=drop_cols)
    return result
