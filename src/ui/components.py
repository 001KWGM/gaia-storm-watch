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
    c1.metric("Peak displayed Hs", fmt(pd.to_numeric(df.get("wave_hs_m"), errors="coerce").max(), "m", 1))
    c2.metric("Highest wind gust", fmt(pd.to_numeric(df.get("wind_gust_kmh"), errors="coerce").max(), "km/h", 0))
    c3.metric("Rainfall total", fmt(pd.to_numeric(df.get("rainfall_mm"), errors="coerce").sum(), "mm", 0))
    c4.metric("Highest residual indicator", fmt(pd.to_numeric(df.get("water_level_residual_m"), errors="coerce").max(), "m", 2))


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
        i = pd.to_numeric(g["wave_hs_m"], errors="coerce").idxmax()
        parts.append(f"The highest displayed significant wave height for {hub_label} is {g.loc[i, 'wave_hs_m']:.1f} m at {pd.to_datetime(g.loc[i, 'timestamp_awst']).strftime('%d %b %Y %H:%M AWST')}.")
    if g["wind_gust_kmh"].notna().any():
        i = pd.to_numeric(g["wind_gust_kmh"], errors="coerce").idxmax()
        parts.append(f"The highest displayed wind gust is {g.loc[i, 'wind_gust_kmh']:.0f} km/h at {pd.to_datetime(g.loc[i, 'timestamp_awst']).strftime('%d %b %Y %H:%M AWST')}.")
    if g["water_level_residual_m"].notna().any():
        i = pd.to_numeric(g["water_level_residual_m"], errors="coerce").idxmax()
        parts.append(f"The highest displayed water-level residual indicator is {g.loc[i, 'water_level_residual_m']:.2f} m. This is an indicator only and is not labelled as storm surge unless independently validated.")
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
                    <h3>{r['hub']}</h3>
                    <p><b>Peak Hs:</b> {r['peak_hs_m']:.1f} m</p>
                    <p><b>Wind gust:</b> {r['peak_wind_gust_kmh']:.0f} km/h</p>
                    <p><b>Rainfall:</b> {r['rainfall_total_mm']:.0f} mm</p>
                    <p><b>Water residual:</b> {r['peak_water_residual_m']:.2f} m</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def interest_form():
    st.markdown("### Request the post-event digest")
    st.caption("Prototype only: this creates a pre-filled email rather than storing personal data in the app.")
    with st.form("interest_form"):
        name = st.text_input("Name")
        company = st.text_input("Company / organisation")
        email = st.text_input("Email")
        consent = st.checkbox("I understand this is a general-interest demonstrator and not official emergency, forecast or safety advice.")
        submitted = st.form_submit_button("Create request email")
    if submitted:
        if not name or not email or not consent:
            st.error("Please add name, email and tick the acknowledgement.")
        else:
            subject = "GAIA Marine Storm Watch digest request"
            body = f"Name: {name}%0ACompany: {company}%0AEmail: {email}%0ARequest: Please send the post-event GAIA Marine Storm Watch digest.%0A"
            st.link_button("Open email request", f"mailto:info@gaia-marine.com.au?subject={subject}&body={body}")
            st.success("Email link created. This avoids storing personal information in the prototype app.")
