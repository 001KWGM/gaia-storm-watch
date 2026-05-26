import streamlit as st
import pandas as pd


def hero(title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="gaia-hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
            <p class="gaia-small">Educational public-data visualisation | General interest only | Not official emergency, forecast or safety advice</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_cards(df: pd.DataFrame):
    c1, c2, c3, c4 = st.columns(4)
    def fmt(v, suffix, dp=1):
        return "N/A" if pd.isna(v) else f"{v:.{dp}f} {suffix}"
    c1.metric("Peak observed Hs", fmt(pd.to_numeric(df.get("wave_hs_m"), errors="coerce").max(), "m", 1))
    c2.metric("Highest wind gust", fmt(pd.to_numeric(df.get("wind_gust_kmh"), errors="coerce").max(), "km/h", 0))
    c3.metric("Rainfall total", fmt(pd.to_numeric(df.get("rainfall_mm"), errors="coerce").sum(), "mm", 0))
    c4.metric("Highest water residual", fmt(pd.to_numeric(df.get("water_level_residual_m"), errors="coerce").max(), "m", 2))


def source_status_table(df: pd.DataFrame):
    status = df.groupby("hub", as_index=False).agg(
        records=("timestamp_awst", "count"),
        first_record_awst=("timestamp_awst", "min"),
        latest_record_awst=("timestamp_awst", "max"),
        source_mode=("source_mode", lambda x: ", ".join(sorted(set(x.dropna().astype(str))))[:120]),
        qa_flags=("qa_flag", lambda x: ", ".join(sorted(set(x.dropna().astype(str))))[:120]),
    )
    st.dataframe(status, use_container_width=True, hide_index=True)


def narrative_summary(df: pd.DataFrame, hub_label: str):
    if df.empty:
        st.info("No records available for this hub.")
        return
    g = df.copy()
    parts = []
    if g["wave_hs_m"].notna().any():
        i = g["wave_hs_m"].astype(float).idxmax()
        parts.append(f"The highest displayed significant wave height for {hub_label} is {g.loc[i, 'wave_hs_m']:.1f} m at {pd.to_datetime(g.loc[i, 'timestamp_awst']).strftime('%d %b %Y %H:%M AWST')}.")
    if g["wind_gust_kmh"].notna().any():
        i = g["wind_gust_kmh"].astype(float).idxmax()
        parts.append(f"The highest displayed wind gust is {g.loc[i, 'wind_gust_kmh']:.0f} km/h at {pd.to_datetime(g.loc[i, 'timestamp_awst']).strftime('%d %b %Y %H:%M AWST')}.")
    if g["water_level_residual_m"].notna().any():
        i = g["water_level_residual_m"].astype(float).idxmax()
        parts.append(f"The highest displayed water-level residual indicator is {g.loc[i, 'water_level_residual_m']:.2f} m. This is an indicator only and is not labelled as storm surge unless independently validated.")
    if parts:
        st.markdown(" ".join(parts))
    else:
        st.info("Not enough numeric data are available to generate a summary.")
