from __future__ import annotations

import html
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui.branding import GAIA_DARK, GAIA_GREY, GAIA_LIGHT_GREY, GAIA_BG, GAIA_GOLD
from src.ui.components import caption, fmt_time, latest_display_time, source_mode_text


def _fmt(value: Any, suffix: str = "", dp: int = 1) -> str:
    try:
        if pd.isna(value):
            return "N/A"
        return f"{float(value):.{dp}f}{suffix}"
    except Exception:
        return "N/A"


def _wind_dir_label(deg: Any) -> str:
    try:
        d = float(deg) % 360
    except Exception:
        return "N/A"
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return f"{dirs[int((d + 11.25) // 22.5) % 16]} ({d:.0f}°)"


def event_phase_for_time(df: pd.DataFrame, selected_time: pd.Timestamp) -> str:
    """Simple storytelling phase label. Not a warning/severity label."""
    g = df.copy()
    g["timestamp_awst"] = pd.to_datetime(g["timestamp_awst"], errors="coerce")
    valid_times = g["timestamp_awst"].dropna().sort_values().unique()
    if len(valid_times) == 0:
        return "Display period unavailable"
    start = pd.Timestamp(valid_times[0])
    end = pd.Timestamp(valid_times[-1])
    span = max((end - start).total_seconds(), 1)
    position = (selected_time - start).total_seconds() / span
    # If the selected time is around the composite event peak, call it peak expression.
    parts = []
    for col in ["wave_hs_m", "wind_gust_kmh", "rainfall_mm", "water_level_residual_m"]:
        if col in g:
            s = pd.to_numeric(g[col], errors="coerce")
            if s.notna().any() and s.max() != s.min():
                parts.append((s - s.min()) / (s.max() - s.min()))
    if parts:
        g["event_index"] = pd.concat(parts, axis=1).mean(axis=1)
        idx = g.groupby("timestamp_awst")["event_index"].mean().idxmax()
        peak = pd.Timestamp(idx)
        if abs((selected_time - peak).total_seconds()) <= 6 * 3600:
            return "Peak-expression window"
    if position < 0.32:
        return "Approach / build-up"
    if position < 0.68:
        return "During-event window"
    return "Aftermath / easing window"


def time_step_selector(df: pd.DataFrame, default: str = "peak") -> pd.Timestamp | None:
    g = df.copy()
    g["timestamp_awst"] = pd.to_datetime(g["timestamp_awst"], errors="coerce")
    times = sorted(g["timestamp_awst"].dropna().unique())
    if not times:
        st.info("No timestamps are available for the time viewer.")
        return None

    labels = [pd.Timestamp(t).strftime("%d %b %Y %H:%M AWST") for t in times]
    default_idx = len(labels) // 2
    if default == "latest":
        default_idx = len(labels) - 1
    elif default == "start":
        default_idx = 0
    elif default == "peak":
        parts = []
        for col in ["wave_hs_m", "wind_gust_kmh", "rainfall_mm", "water_level_residual_m"]:
            if col in g:
                s = pd.to_numeric(g[col], errors="coerce")
                if s.notna().any() and s.max() != s.min():
                    parts.append((s - s.min()) / (s.max() - s.min()))
        if parts:
            g["event_index"] = pd.concat(parts, axis=1).mean(axis=1)
            peak_time = g.groupby("timestamp_awst")["event_index"].mean().idxmax()
            try:
                default_idx = times.index(peak_time)
            except ValueError:
                default_idx = len(labels) // 2

    selected_label = st.select_slider(
        "Select display timestamp",
        options=labels,
        value=labels[default_idx],
        help="Public viewer control only. GAIA Marine controls all source selection, data preparation and dashboard settings.",
    )
    return pd.Timestamp(times[labels.index(selected_label)])


def timestamp_snapshot(df: pd.DataFrame, selected_time: pd.Timestamp) -> pd.DataFrame:
    g = df.copy()
    g["timestamp_awst"] = pd.to_datetime(g["timestamp_awst"], errors="coerce")
    # Use exact aligned timestep when available. If a hub has no exact record, nearest within 90 minutes is used and flagged.
    rows = []
    for hub, h in g.groupby("hub"):
        exact = h[h["timestamp_awst"] == selected_time]
        if not exact.empty:
            r = exact.iloc[0].to_dict()
            r["viewer_match"] = "Exact aligned timestamp"
        else:
            h = h.dropna(subset=["timestamp_awst"]).copy()
            if h.empty:
                continue
            h["_dt_seconds"] = (h["timestamp_awst"] - selected_time).abs().dt.total_seconds()
            nearest = h.sort_values("_dt_seconds").iloc[0]
            r = nearest.to_dict()
            r["viewer_match"] = "Nearest available record" if nearest["_dt_seconds"] <= 5400 else "No close record"
        rows.append(r)
    out = pd.DataFrame(rows)
    if not out.empty:
        out["timestamp_awst"] = pd.to_datetime(out["timestamp_awst"], errors="coerce")
    return out


def snapshot_cards(snap: pd.DataFrame, selected_time: pd.Timestamp):
    st.markdown("### Time-step snapshot")
    st.markdown(
        f"<div class='story-panel'><h3>{html.escape(selected_time.strftime('%d %b %Y %H:%M AWST'))}</h3>"
        f"<p>All displayed values below are aligned to the selected dashboard timestamp where available. This is a public-interest snapshot, not a decision-support screen.</p></div>",
        unsafe_allow_html=True,
    )
    if snap.empty:
        st.info("No records are available for this timestamp.")
        return
    cols = st.columns(min(4, len(snap)))
    for i, (_, r) in enumerate(snap.iterrows()):
        with cols[i % len(cols)]:
            st.markdown(
                f"""
                <div class="gaia-card">
                    <h3>{html.escape(str(r.get('display_name', r.get('hub', 'Hub'))))}</h3>
                    <p class="gaia-small">Record: {html.escape(fmt_time(r.get('timestamp_awst')))} · {html.escape(str(r.get('viewer_match', '')))}</p>
                    <p><b>Wave Hs:</b> {_fmt(r.get('wave_hs_m'), ' m', 1)} &nbsp; <b>Hmax:</b> {_fmt(r.get('wave_hmax_m'), ' m', 1)}</p>
                    <p><b>Wind gust:</b> {_fmt(r.get('wind_gust_kmh'), ' km/h', 0)} &nbsp; <b>Dir:</b> {html.escape(_wind_dir_label(r.get('wind_direction_deg')))}</p>
                    <p><b>Rain:</b> {_fmt(r.get('rainfall_mm'), ' mm', 1)} &nbsp; <b>Pressure:</b> {_fmt(r.get('air_pressure_hpa'), ' hPa', 0)}</p>
                    <p><b>Water level:</b> {_fmt(r.get('water_level_m'), ' m', 2)} &nbsp; <b>Residual:</b> {_fmt(r.get('water_level_residual_m'), ' m', 2)}</p>
                    <p class="gaia-small">Status: {html.escape(str(r.get('data_status', '')))} · Source: {html.escape(str(r.get('source_mode', '')))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    caption(f"Cards: selected-time values by coastal hub. Source mode: {source_mode_text(snap)}. Selected timestamp: {selected_time.strftime('%d %b %Y %H:%M AWST')}. Camera, radar and weather-reference pages retain their own official timestamps when opened externally.")


def snapshot_chart(snap: pd.DataFrame, selected_time: pd.Timestamp):
    if snap.empty:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=snap["hub"], y=pd.to_numeric(snap["wave_hs_m"], errors="coerce"), name="Hs (m)", marker_color=GAIA_GOLD))
    fig.add_trace(go.Bar(x=snap["hub"], y=pd.to_numeric(snap["wind_gust_kmh"], errors="coerce") / 20.0, name="Wind gust / 20", marker_color=GAIA_DARK))
    fig.add_trace(go.Bar(x=snap["hub"], y=pd.to_numeric(snap["rainfall_mm"], errors="coerce"), name="Rainfall (mm)", marker_color=GAIA_LIGHT_GREY))
    fig.update_layout(
        title=f"Selected timestamp comparison — {selected_time.strftime('%d %b %Y %H:%M AWST')}",
        barmode="group",
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.63)",
        font=dict(color=GAIA_DARK, size=12),
        margin=dict(l=46, r=28, t=52, b=52),
        legend=dict(orientation="h", yanchor="bottom", y=-0.24, xanchor="center", x=0.5),
    )
    fig.update_yaxes(title="Display-scaled values")
    fig.update_xaxes(title="Coastal hub")
    return fig


def snapshot_table(snap: pd.DataFrame) -> pd.DataFrame:
    if snap.empty:
        return snap
    cols = [
        "hub", "timestamp_awst", "viewer_match", "wave_hs_m", "wave_hmax_m", "wave_tp_s",
        "wind_gust_kmh", "wind_direction_deg", "rainfall_mm", "air_pressure_hpa",
        "water_level_m", "water_level_residual_m", "data_status", "qa_flag", "source_mode",
    ]
    out = snap[[c for c in cols if c in snap.columns]].copy()
    if "timestamp_awst" in out:
        out["timestamp_awst"] = out["timestamp_awst"].apply(fmt_time)
    rename = {
        "hub": "Hub",
        "timestamp_awst": "Record time",
        "viewer_match": "Time match",
        "wave_hs_m": "Hs (m)",
        "wave_hmax_m": "Hmax (m)",
        "wave_tp_s": "Tp (s)",
        "wind_gust_kmh": "Wind gust (km/h)",
        "wind_direction_deg": "Wind dir (deg)",
        "rainfall_mm": "Rainfall (mm)",
        "air_pressure_hpa": "Pressure (hPa)",
        "water_level_m": "Water level (m)",
        "water_level_residual_m": "Residual indicator (m)",
        "data_status": "Data status",
        "qa_flag": "QA flag",
        "source_mode": "Source mode",
    }
    return out.rename(columns=rename)


def render_time_viewer(df: pd.DataFrame, event: dict, public_cfg: dict):
    st.subheader("Timestamp viewer")
    st.markdown(
        "Move through the event timeline and view the same timestamp across the available coastal hubs. "
        "This is intended as the main public exploration screen: one selected time, one aligned snapshot, then summary tabs elsewhere for the full event story."
    )
    selected = time_step_selector(df, public_cfg.get("default_time_viewer_position", "peak"))
    if selected is None:
        return
    phase = event_phase_for_time(df, selected)
    c1, c2, c3 = st.columns(3)
    c1.metric("Selected time", selected.strftime("%d %b %H:%M AWST"))
    c2.metric("Story phase", phase)
    c3.metric("Displayed hubs", str(df["hub"].nunique() if "hub" in df else 0))
    caption(f"Timestamp selector: public viewer control for stepping through the curated display record. Event window: {event.get('start_awst', 'configured start')} to {event.get('end_awst', 'configured end')}. All source preparation and time alignment are controlled internally by GAIA Marine.")
    snap = timestamp_snapshot(df, selected)
    snapshot_cards(snap, selected)
    st.plotly_chart(snapshot_chart(snap, selected), use_container_width=True)
    caption("Graph: selected timestamp comparison. Wind gust is scaled by 20 so it can sit visually beside wave height and rainfall in a compact public snapshot. Refer to the cards/table for actual units.")
    with st.expander("Selected timestamp data table", expanded=True):
        st.dataframe(snapshot_table(snap), use_container_width=True, hide_index=True)
        caption(f"Table: all dashboard values available for the selected timestamp. Source mode: {source_mode_text(snap)}. Selected timestamp: {selected.strftime('%d %b %Y %H:%M AWST')}.")
