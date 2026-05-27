from __future__ import annotations

import html
import pandas as pd
import streamlit as st


def fmt_time(value) -> str:
    try:
        if pd.isna(value):
            return "not available"
        return pd.to_datetime(value).strftime("%d %b %Y %H:%M AWST")
    except Exception:
        return "not available"


def latest_display_time(df: pd.DataFrame) -> str:
    if df.empty or "timestamp_awst" not in df:
        return "not available"
    return fmt_time(pd.to_datetime(df["timestamp_awst"], errors="coerce").max())


def source_mode_text(df: pd.DataFrame) -> str:
    if df.empty or "source_mode" not in df:
        return "source not available"
    vals = sorted(set(df["source_mode"].dropna().astype(str)))
    return ", ".join(vals) if vals else "source not available"


def caption(text: str):
    st.markdown(f'<div class="caption-box">{html.escape(text)}</div>', unsafe_allow_html=True)


def hero(title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="gaia-hero">
            <h1>{html.escape(title)}</h1>
            <p>{html.escape(subtitle)}</p>
            <p>Technology-driven public storm-event visualisation across coastal and offshore environments.</p>
            <div class="tags">
                <span>Metocean</span><span>Coastal conditions</span><span>Data engineering</span><span>General interest</span>
            </div>
            <p class="gaia-small" style="margin-top:0.75rem;">Educational public-data visualisation · Not official emergency, forecast, marine-safety, operational or commercial decision advice</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_cards(df: pd.DataFrame):
    c1, c2, c3, c4 = st.columns(4)
    def fmt(v, suffix, dp=1):
        return "N/A" if pd.isna(v) else f"{v:.{dp}f} {suffix}"
    c1.metric("Peak displayed Hs", fmt(pd.to_numeric(df.get("wave_hs_m"), errors="coerce").max(), "m", 1))
    c2.metric("Highest wind gust", fmt(pd.to_numeric(df.get("wind_gust_kmh"), errors="coerce").max(), "km/h", 0))
    c3.metric("Rainfall total", fmt(pd.to_numeric(df.get("rainfall_mm"), errors="coerce").sum(), "mm", 0))
    c4.metric("Highest residual indicator", fmt(pd.to_numeric(df.get("water_level_residual_m"), errors="coerce").max(), "m", 2))
    caption(f"Summary cards show highest or cumulative values from the curated dashboard dataset. Source mode: {source_mode_text(df)}. Latest displayed timestamp: {latest_display_time(df)}.")


def source_status_table(df: pd.DataFrame):
    status = df.groupby("hub", as_index=False).agg(
        records=("timestamp_awst", "count"),
        first_record_awst=("timestamp_awst", "min"),
        latest_record_awst=("timestamp_awst", "max"),
        source_mode=("source_mode", lambda x: ", ".join(sorted(set(x.dropna().astype(str))))[:160]),
        qa_flags=("qa_flag", lambda x: ", ".join(sorted(set(x.dropna().astype(str))))[:160]),
    )
    st.dataframe(status, use_container_width=True, hide_index=True)
    caption("Source-status table showing the displayed record span, source mode and QA flag summary by coastal hub. Times are shown in AWST where available.")


def narrative_summary(df: pd.DataFrame, hub_label: str):
    if df.empty:
        st.info("No records available for this hub.")
        return
    g = df.copy()
    parts = []
    if g["wave_hs_m"].notna().any():
        i = pd.to_numeric(g["wave_hs_m"], errors="coerce").idxmax()
        parts.append(f"The highest displayed significant wave height for {hub_label} is {g.loc[i, 'wave_hs_m']:.1f} m at {fmt_time(g.loc[i, 'timestamp_awst'])}.")
    if g["wind_gust_kmh"].notna().any():
        i = pd.to_numeric(g["wind_gust_kmh"], errors="coerce").idxmax()
        parts.append(f"The highest displayed wind gust is {g.loc[i, 'wind_gust_kmh']:.0f} km/h at {fmt_time(g.loc[i, 'timestamp_awst'])}.")
    if g["water_level_residual_m"].notna().any():
        i = pd.to_numeric(g["water_level_residual_m"], errors="coerce").idxmax()
        parts.append(f"The highest displayed water-level residual indicator is {g.loc[i, 'water_level_residual_m']:.2f} m at {fmt_time(g.loc[i, 'timestamp_awst'])}. This is an indicator only and is not labelled as storm surge unless independently validated.")
    if parts:
        st.markdown(" ".join(parts))
    else:
        st.info("Not enough numeric data are available to generate a summary.")


def insight_cards(snapshot: pd.DataFrame):
    if snapshot.empty:
        st.info("No snapshot available.")
        return
    cols = st.columns(min(4, len(snapshot)))
    for i, (_, r) in enumerate(snapshot.iterrows()):
        with cols[i % len(cols)]:
            st.markdown(
                f"""
                <div class="gaia-card">
                    <h3>{html.escape(str(r['hub']))}</h3>
                    <p><b>Peak Hs:</b> {r['peak_hs_m']:.1f} m</p>
                    <p><b>Wind gust:</b> {r['peak_wind_gust_kmh']:.0f} km/h</p>
                    <p><b>Rainfall:</b> {r['rainfall_total_mm']:.0f} mm</p>
                    <p><b>Water residual:</b> {r['peak_water_residual_m']:.2f} m</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    caption("Coastal hub cards summarise the highest displayed values in the curated event dataset. These are general-interest values only, not warning levels or operational thresholds.")


def storm_story_panel(event_name: str, data_mode: str):
    st.markdown(
        f"""
        <div class="story-panel">
            <h3>Holistic storm event story</h3>
            <p><b>{html.escape(event_name)}</b> is framed as a simple before–during–after visual story: weather build-up, changing coastal conditions, peak displayed values, and the easing phase after the event.</p>
            <p>This is a curated public display for interest and brand awareness. GAIA Marine controls the source choices, thresholds, processing settings and updates internally.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def quick_story_tiles(df: pd.DataFrame):
    if df.empty:
        return
    g = df.copy()
    g["timestamp_awst"] = pd.to_datetime(g["timestamp_awst"], errors="coerce")
    latest_time = g["timestamp_awst"].max()
    first_time = g["timestamp_awst"].min()
    wave_peak = pd.to_numeric(g.get("wave_hs_m"), errors="coerce").max()
    wind_peak = pd.to_numeric(g.get("wind_gust_kmh"), errors="coerce").max()
    rain_total = pd.to_numeric(g.get("rainfall_mm"), errors="coerce").sum()
    cols = st.columns(4)
    items = [
        ("Event window", f"{first_time.strftime('%d %b')} – {latest_time.strftime('%d %b')}" if pd.notna(first_time) and pd.notna(latest_time) else "N/A", "Displayed time span"),
        ("Peak displayed waves", "N/A" if pd.isna(wave_peak) else f"{wave_peak:.1f} m", "Highest Hs in displayed data"),
        ("Peak displayed gust", "N/A" if pd.isna(wind_peak) else f"{wind_peak:.0f} km/h", "Highest gust in displayed data"),
        ("Displayed rainfall", "N/A" if pd.isna(rain_total) else f"{rain_total:.0f} mm", "Across all displayed hubs"),
    ]
    for col, (label, value, note) in zip(cols, items):
        with col:
            st.markdown(f"""<div class="gaia-card"><div class="metric-label">{html.escape(label)}</div><div class="metric-value">{html.escape(value)}</div><p class="gaia-small">{html.escape(note)}</p></div>""", unsafe_allow_html=True)
    caption(f"Top-level event tiles are generated from the curated displayed dataset. Source mode: {source_mode_text(df)}. Latest displayed timestamp: {latest_display_time(df)}.")
