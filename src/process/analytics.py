from __future__ import annotations

import pandas as pd


def _num(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(df[col], errors="coerce")


def peak_row(df: pd.DataFrame, metric: str) -> dict | None:
    s = _num(df, metric)
    if s.empty or not s.notna().any():
        return None
    idx = s.idxmax()
    row = df.loc[idx].to_dict()
    row[metric] = float(s.loc[idx])
    return row


def coverage_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    required = [
        ("Wave Hs", "wave_hs_m"),
        ("Wind gust", "wind_gust_kmh"),
        ("Rainfall", "rainfall_mm"),
        ("Water level", "water_level_m"),
        ("Water residual", "water_level_residual_m"),
    ]
    for hub, g in df.groupby("hub"):
        recs = len(g)
        for label, col in required:
            available = int(_num(g, col).notna().sum()) if col in g.columns else 0
            rows.append({
                "hub": hub,
                "dataset": label,
                "records": recs,
                "available_records": available,
                "coverage_percent": round((available / recs * 100), 1) if recs else 0.0,
            })
    return pd.DataFrame(rows)


def hub_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for hub, g in df.groupby("hub"):
        g = g.sort_values("timestamp_awst")
        latest = g.iloc[-1]
        rows.append({
            "hub": hub,
            "latest_awst": latest.get("timestamp_awst"),
            "peak_hs_m": _num(g, "wave_hs_m").max(),
            "peak_wind_gust_kmh": _num(g, "wind_gust_kmh").max(),
            "rainfall_total_mm": _num(g, "rainfall_mm").sum(),
            "peak_water_residual_m": _num(g, "water_level_residual_m").max(),
            "records": len(g),
            "source_mode": ", ".join(sorted(set(g.get("source_mode", pd.Series(dtype=str)).dropna().astype(str))))[:140],
        })
    out = pd.DataFrame(rows)
    for c in ["peak_hs_m", "peak_wind_gust_kmh", "rainfall_total_mm", "peak_water_residual_m"]:
        out[c] = pd.to_numeric(out[c], errors="coerce").round(2)
    return out


def threshold_events(df: pd.DataFrame) -> pd.DataFrame:
    checks = [
        ("Hs ≥ 2.0 m", "wave_hs_m", 2.0, ">="),
        ("Hs ≥ 3.0 m", "wave_hs_m", 3.0, ">="),
        ("Wind gust ≥ 70 km/h", "wind_gust_kmh", 70.0, ">="),
        ("Wind gust ≥ 90 km/h", "wind_gust_kmh", 90.0, ">="),
        ("Rain interval ≥ 10 mm", "rainfall_mm", 10.0, ">="),
        ("Water residual ≥ 0.20 m", "water_level_residual_m", 0.20, ">="),
        ("Water residual ≥ 0.35 m", "water_level_residual_m", 0.35, ">="),
    ]
    rows = []
    for hub, g in df.groupby("hub"):
        for label, col, val, op in checks:
            s = _num(g, col)
            if s.empty or not s.notna().any():
                continue
            mask = s >= val
            rows.append({
                "hub": hub,
                "indicator": label,
                "records_meeting_indicator": int(mask.sum()),
                "first_time_awst": g.loc[mask, "timestamp_awst"].min() if mask.any() else pd.NaT,
                "last_time_awst": g.loc[mask, "timestamp_awst"].max() if mask.any() else pd.NaT,
                "maximum_value": round(float(s.max()), 2),
                "note": "General-interest event indicator only; not a warning threshold.",
            })
    return pd.DataFrame(rows)


def event_digest_markdown(df: pd.DataFrame, app_title: str = "GAIA Marine Storm Watch") -> str:
    df = df.copy()
    df["timestamp_awst"] = pd.to_datetime(df["timestamp_awst"], errors="coerce")
    first = df["timestamp_awst"].min()
    last = df["timestamp_awst"].max()
    lines = [
        f"# {app_title} — Public Event Digest",
        "",
        "This digest is a general-interest public-data visualisation summary prepared by GAIA Marine. It is not an official forecast, warning, emergency advice product, marine safety tool, or operational decision-support system.",
        "",
        f"Displayed period: {first.strftime('%d %b %Y %H:%M AWST') if pd.notna(first) else 'N/A'} to {last.strftime('%d %b %Y %H:%M AWST') if pd.notna(last) else 'N/A'}.",
        "",
        "## Hub summary",
        "",
    ]
    snap = hub_snapshot(df)
    for _, r in snap.iterrows():
        lines.append(f"### {r['hub']}")
        lines.append(f"- Peak significant wave height shown: {r['peak_hs_m']:.1f} m")
        lines.append(f"- Highest wind gust shown: {r['peak_wind_gust_kmh']:.0f} km/h")
        lines.append(f"- Rainfall total shown: {r['rainfall_total_mm']:.0f} mm")
        lines.append(f"- Highest water-level residual indicator shown: {r['peak_water_residual_m']:.2f} m")
        lines.append("")
    lines.extend([
        "## Important limitations",
        "",
        "Displayed values are based on the datasets loaded into the demonstrator. Source data may be provisional, incomplete, delayed, unverified or subject to agency-specific conditions of use. Water-level residual indicators are not labelled as storm surge unless independently validated against an appropriate predicted tide and datum basis.",
        "",
        "For official warnings, forecasts and emergency information, refer directly to the Bureau of Meteorology, Emergency WA, local authorities and relevant marine safety agencies.",
    ])
    return "\n".join(lines)
