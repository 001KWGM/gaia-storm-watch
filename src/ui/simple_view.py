from __future__ import annotations

import html
from typing import Any
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.ui.branding import GAIA_DARK, GAIA_GREY, GAIA_LIGHT_GREY, GAIA_GOLD
from src.ui.components import caption, fmt_time, source_mode_text, latest_display_time


def cap_to_latest_available(df: pd.DataFrame, public_cfg: dict[str, Any] | None = None) -> pd.DataFrame:
    """Keep the public app honest: do not show future timestamps as observed/displayed records."""
    if df.empty or "timestamp_awst" not in df:
        return df
    g = df.copy()
    g["timestamp_awst"] = pd.to_datetime(g["timestamp_awst"], errors="coerce")
    g = g.dropna(subset=["timestamp_awst"])
    now_awst = pd.Timestamp.now(tz="Australia/Perth").floor("h")
    data_max = g["timestamp_awst"].max()
    # If data are timezone-naive after CSV handling, localise defensively.
    if data_max.tzinfo is None:
        now_awst = now_awst.tz_localize(None)
    cap = min(data_max, now_awst)
    return g[g["timestamp_awst"] <= cap].sort_values(["hub", "timestamp_awst"])


def _fmt_num(value, suffix: str, dp: int = 1) -> str:
    try:
        if pd.isna(value):
            return "N/A"
        return f"{float(value):.{dp}f} {suffix}".strip()
    except Exception:
        return "N/A"


def render_time_slider(df: pd.DataFrame, public_cfg: dict[str, Any] | None = None):
    times = sorted(pd.to_datetime(df["timestamp_awst"], errors="coerce").dropna().unique())
    times = [pd.Timestamp(t) for t in times]
    if not times:
        return pd.Timestamp.now(tz="Australia/Perth").floor("h")
    default_mode = (public_cfg or {}).get("default_time_viewer_position", "latest")
    if default_mode == "peak" and "wave_hs_m" in df:
        try:
            agg = df.groupby("timestamp_awst")["wave_hs_m"].mean(numeric_only=True)
            default_time = pd.Timestamp(agg.idxmax()) if not agg.empty else times[-1]
        except Exception:
            default_time = times[-1]
    else:
        default_time = times[-1]
    if default_time not in times:
        default_time = times[-1]
    return st.select_slider("Time", options=times, value=default_time, format_func=lambda x: pd.Timestamp(x).strftime("%d %b %H:%M"))


def render_snapshot_cards(row: pd.Series, selected_time):
    cols = st.columns(4)
    items = [
        ("Wave Hs", _fmt_num(row.get("wave_hs_m"), "m", 1), "Significant wave height"),
        ("Wind gust", _fmt_num(row.get("wind_gust_kmh"), "km/h", 0), "Displayed wind context"),
        ("Rainfall", _fmt_num(row.get("rainfall_mm"), "mm", 1), "Interval rainfall"),
        ("Water level", _fmt_num(row.get("water_level_m"), "m", 2), "Observed/displayed level"),
    ]
    for col, (label, value, note) in zip(cols, items):
        with col:
            st.markdown(f"""
            <div class="gaia-card">
                <div class="metric-label">{html.escape(label)}</div>
                <div class="metric-value">{html.escape(value)}</div>
                <p class="gaia-small">{html.escape(note)}</p>
            </div>
            """, unsafe_allow_html=True)
    st.markdown(
        f"<p class='gaia-small'><b>Source/status:</b> {html.escape(str(row.get('source_mode', 'not specified')))} · {html.escape(str(row.get('data_status', 'not specified')))} · Timestamp {pd.Timestamp(selected_time).strftime('%d %b %Y %H:%M AWST')}</p>",
        unsafe_allow_html=True,
    )
    caption("Cards: selected location values at the selected dashboard timestamp. Source: curated GAIA Marine display dataset. Timestamp: selected AWST time shown above. Values are for general-interest viewing only.")


def render_weather_reference_strip(refs: list[dict]):
    if not refs:
        st.info("No official weather reference links configured.")
        return
    priority = []
    for key in ["warning", "radar", "rain", "synoptic", "satellite", "emergency"]:
        for r in refs:
            hay = f"{r.get('name','')} {r.get('type','')} {r.get('role','')}".lower()
            if key in hay and r not in priority:
                priority.append(r)
    if not priority:
        priority = refs
    priority = priority[:6]
    cols = st.columns(3)
    for i, item in enumerate(priority):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="gaia-card">
                <h3>{html.escape(str(item.get('name','Official source')))}</h3>
                <p>{html.escape(str(item.get('role','Official external reference.')))}</p>
                <p class="gaia-small"><b>Source:</b> {html.escape(str(item.get('source','Official external source')))}</p>
                <p class="gaia-small"><b>Timestamp:</b> {html.escape(str(item.get('time_alignment','Shown on official source page where available')))}</p>
            </div>
            """, unsafe_allow_html=True)
            st.link_button("Open", item.get("url", "https://www.bom.gov.au/"))
    caption("Weather context: official external weather, radar, rainfall, warning, satellite or synoptic references. Source timestamps/validity are shown on the official source pages where available. GAIA Marine links to these products and does not rehost them.")


def render_camera_strip(cams: list[dict], selected_hub: str):
    hub_cams = [c for c in cams if c.get("hub") == selected_hub]
    if not hub_cams:
        st.info("No official camera links configured for this location.")
        return
    cols = st.columns(min(2, len(hub_cams)))
    for i, cam in enumerate(hub_cams[:4]):
        with cols[i % len(cols)]:
            st.markdown(f"""
            <div class="gaia-card cam-card">
                <h3>{html.escape(str(cam.get('name','Coast camera')))}</h3>
                <p>{html.escape(str(cam.get('view_note','Official coast camera page.')))}</p>
                <p class="gaia-small"><b>Source:</b> {html.escape(str(cam.get('source','WA DTMI coast cam')))}</p>
                <p class="gaia-small"><b>Image timestamp:</b> shown on official source page where available.</p>
            </div>
            """, unsafe_allow_html=True)
            st.link_button("View camera", cam.get("official_url", "#"))
    caption("Coast camera context: official source camera pages for the selected location. GAIA Marine does not scrape, store, archive or republish third-party camera images in this public display.")


def render_simple_timeline(df: pd.DataFrame, hub_label: str, selected_time):
    g = df.sort_values("timestamp_awst").copy()
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.09,
                        subplot_titles=("Waves and wind", "Rainfall and water level"), specs=[[{"secondary_y": True}], [{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=g["timestamp_awst"], y=g["wave_hs_m"], name="Wave Hs (m)", line=dict(color=GAIA_GOLD, width=2.4)), row=1, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=g["timestamp_awst"], y=g["wind_gust_kmh"], name="Wind gust (km/h)", line=dict(color=GAIA_DARK, width=2)), row=1, col=1, secondary_y=True)
    fig.add_trace(go.Bar(x=g["timestamp_awst"], y=g["rainfall_mm"], name="Rainfall (mm)", marker_color=GAIA_LIGHT_GREY), row=2, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=g["timestamp_awst"], y=g["water_level_m"], name="Water level (m)", line=dict(color=GAIA_GREY, width=2)), row=2, col=1, secondary_y=True)
    fig.add_vline(x=selected_time, line_width=2, line_dash="dash", line_color=GAIA_DARK)
    fig.update_layout(
        title=f"{hub_label}: event trend to latest displayed record",
        height=570,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.65)",
        font=dict(color=GAIA_DARK, size=12),
        margin=dict(l=46, r=40, t=70, b=55),
        legend=dict(orientation="h", yanchor="bottom", y=-0.23, xanchor="center", x=0.5),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(45,58,76,0.12)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(45,58,76,0.12)", zeroline=False)
    fig.update_yaxes(title_text="m", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="km/h", row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="mm", row=2, col=1, secondary_y=False)
    fig.update_yaxes(title_text="m", row=2, col=1, secondary_y=True)
    return fig


def render_location_stats(df: pd.DataFrame, selected_hub: str, hub_label: str):
    if df.empty:
        st.info("No records available for this location.")
        return
    cols = st.columns(4)
    peak_hs = pd.to_numeric(df.get("wave_hs_m"), errors="coerce").max()
    peak_gust = pd.to_numeric(df.get("wind_gust_kmh"), errors="coerce").max()
    rain_total = pd.to_numeric(df.get("rainfall_mm"), errors="coerce").sum()
    latest = pd.to_datetime(df["timestamp_awst"], errors="coerce").max()
    items = [
        ("Peak Hs", _fmt_num(peak_hs, "m", 1), "Highest displayed wave height"),
        ("Peak gust", _fmt_num(peak_gust, "km/h", 0), "Highest displayed gust"),
        ("Rainfall", _fmt_num(rain_total, "mm", 0), "Displayed cumulative rainfall"),
        ("Latest record", latest.strftime("%d %b %H:%M") if pd.notna(latest) else "N/A", "Latest displayed timestamp"),
    ]
    for col, (label, value, note) in zip(cols, items):
        with col:
            st.markdown(f"""<div class="gaia-card"><div class="metric-label">{html.escape(label)}</div><div class="metric-value">{html.escape(value)}</div><p class="gaia-small">{html.escape(note)}</p></div>""", unsafe_allow_html=True)
    caption(f"Location summary: highest or cumulative displayed values for {hub_label}, capped at latest available dashboard record. Source mode: {source_mode_text(df)}. Latest displayed timestamp: {latest_display_time(df)}.")


def render_all_locations_table(snapshot_all: pd.DataFrame):
    cols = ["hub", "wave_hs_m", "wind_gust_kmh", "rainfall_mm", "water_level_m", "data_status", "source_mode"]
    show = snapshot_all[[c for c in cols if c in snapshot_all.columns]].copy()
    rename = {
        "hub": "Location", "wave_hs_m": "Hs (m)", "wind_gust_kmh": "Gust (km/h)",
        "rainfall_mm": "Rainfall (mm)", "water_level_m": "Water level (m)",
        "data_status": "Status", "source_mode": "Source mode",
    }
    show = show.rename(columns=rename)
    for c in ["Hs (m)", "Gust (km/h)", "Rainfall (mm)", "Water level (m)"]:
        if c in show:
            show[c] = pd.to_numeric(show[c], errors="coerce").round(2)
    st.dataframe(show, use_container_width=True, hide_index=True)


def render_source_expanders(master: pd.DataFrame, sources: dict, refs: list[dict], cams: list[dict]):
    with st.expander("Sources, copyright and limitations", expanded=False):
        st.markdown(
            "This public display is a curated general-interest visualisation. It is not official emergency, forecast, marine-safety, operational or commercial decision advice. "
            "Future timestamps are not displayed as observations; graphs are capped at the latest available dashboard record."
        )
        st.markdown("**Displayed dataset**")
        st.write(f"Source mode: {source_mode_text(master)}")
        st.write(f"Latest displayed timestamp: {latest_display_time(master)}")
        rows = []
        for key, item in (sources or {}).get("sources", {}).items():
            rows.append({
                "Source": item.get("display_name", key),
                "Use": item.get("use_in_prototype", ""),
                "Link": item.get("public_link", ""),
                "Caveat": item.get("caveat", ""),
            })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        caption("Source register: source choices are controlled internally by GAIA Marine. External information remains subject to each source agency's terms, copyright, disclaimers and conditions of use.")
    with st.expander("Camera and weather reference handling", expanded=False):
        st.markdown(
            "Weather maps, radar, rainfall, satellite, warning and coast camera products are treated as official external references. "
            "GAIA Marine links to official source pages and does not rehost BOM/agency weather-map products or third-party camera images in this public display."
        )
        if refs:
            st.markdown("**Weather references configured**")
            st.dataframe(pd.DataFrame(refs), use_container_width=True, hide_index=True)
        if cams:
            st.markdown("**Camera references configured**")
            st.dataframe(pd.DataFrame(cams), use_container_width=True, hide_index=True)
        caption("Reference handling: timestamps for external weather-map and camera products are shown on the official source pages where available. Dashboard timestamps remain AWST.")
