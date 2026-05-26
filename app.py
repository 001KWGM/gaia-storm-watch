from __future__ import annotations

import pandas as pd
import streamlit as st

from src.process.build_master import build_demo_master, normalize_uploaded_file, save_master
from src.ui.branding import css
from src.ui.components import hero, kpi_cards, source_status_table, narrative_summary
from src.ui.charts import storm_timeline, compare_hubs, peak_timing_strip
from src.ui.disclaimers import top_disclaimer, footer_disclaimer
from src.utils.config import load_hubs, load_sources

st.set_page_config(
    page_title="GAIA Marine Storm Watch",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(css(), unsafe_allow_html=True)

cfg = load_hubs()
sources = load_sources()
EVENT = cfg["event"]
HUBS = cfg["hubs"]

hero(EVENT["public_name"], EVENT["subtitle"])
top_disclaimer()

with st.sidebar:
    st.header("Prototype controls")
    st.caption("Use demo data first. Upload public-source CSVs later once the column structure is confirmed.")
    use_demo = st.toggle("Use synthetic demo data", value=True)
    uploads = st.file_uploader(
        "Optional CSV upload(s)", type=["csv"], accept_multiple_files=True,
        help="Accepted columns are flexible: timestamp/date/time, hub/site/station, hs/Hm0, wind gust, rain, pressure, tide/water level, residual/surge etc."
    )
    st.markdown("---")
    st.link_button("Official BOM warnings", "https://www.bom.gov.au/wa/warnings/")
    st.link_button("Emergency WA", "https://www.emergency.wa.gov.au/")
    st.link_button("WA coastal data", "https://www.transport.wa.gov.au/marine/coastal-data-charts.asp")

@st.cache_data(show_spinner=False)
def get_demo():
    return build_demo_master()

frames = []
errors = []
if use_demo:
    frames.append(get_demo())

if uploads:
    for f in uploads:
        try:
            frames.append(normalize_uploaded_file(f))
        except Exception as exc:
            errors.append(f"{f.name}: {exc}")

if not frames:
    st.warning("No data selected. Turn on demo data or upload one or more CSV files.")
    st.stop()

master = pd.concat(frames, ignore_index=True)
# Avoid duplicate exact records when uploaded data and demo data overlap.
master["timestamp_awst"] = pd.to_datetime(master["timestamp_awst"], errors="coerce")
master = master.dropna(subset=["timestamp_awst"])
master = master.sort_values(["hub", "timestamp_awst"])
save_master(master)

if errors:
    with st.expander("Upload issues", expanded=True):
        for err in errors:
            st.error(err)

source_modes = sorted(master["source_mode"].dropna().astype(str).unique())
if any("Synthetic" in s for s in source_modes):
    st.info("Prototype is currently showing synthetic demonstration data. Replace with uploaded public-source data before external publication.")

# Overview metrics
st.subheader("Event snapshot")
kpi_cards(master)

# Simple hub map / locator table
map_df = pd.DataFrame([
    {"hub": h, "display_name": m["display_name"], "lat": m["lat"], "lon": m["lon"], "region": m["region"]}
    for h, m in HUBS.items()
])
left, right = st.columns([1.1, 1])
with left:
    st.map(map_df.rename(columns={"lat": "latitude", "lon": "longitude"}), latitude="latitude", longitude="longitude", size=90, color="#E4C21C")
with right:
    latest = master.groupby("hub", as_index=False).agg(
        latest_awst=("timestamp_awst", "max"),
        peak_hs_m=("wave_hs_m", "max"),
        peak_gust_kmh=("wind_gust_kmh", "max"),
        rainfall_total_mm=("rainfall_mm", "sum"),
    )
    st.dataframe(latest, use_container_width=True, hide_index=True)

tabs = st.tabs(["Storm timeline", "Coastal hubs", "Data sources", "About"])

with tabs[0]:
    st.subheader("Storm timeline")
    hub = st.selectbox("Select coastal hub", sorted(master["hub"].dropna().unique()), key="timeline_hub")
    hub_label = HUBS.get(hub, {}).get("display_name", hub)
    g = master[master["hub"] == hub]
    narrative_summary(g, hub_label)
    st.plotly_chart(storm_timeline(g, hub_label), use_container_width=True)

with tabs[1]:
    st.subheader("Coastal hub comparison")
    metric_options = {
        "Significant wave height Hs (m)": "wave_hs_m",
        "Wind gust (km/h)": "wind_gust_kmh",
        "Rainfall per interval (mm)": "rainfall_mm",
        "Water-level residual indicator (m)": "water_level_residual_m",
    }
    selected_label = st.selectbox("Metric", list(metric_options.keys()))
    selected_metric = metric_options[selected_label]
    st.plotly_chart(compare_hubs(master, selected_metric, selected_label), use_container_width=True)
    st.plotly_chart(peak_timing_strip(master), use_container_width=True)

with tabs[2]:
    st.subheader("Data transparency")
    st.markdown("This tab is deliberately visible. It shows data currency, source mode and caveats rather than hiding limitations.")
    source_status_table(master)
    st.markdown("### Source register")
    source_rows = []
    for key, item in sources["sources"].items():
        source_rows.append({
            "source": item["display_name"],
            "prototype_use": item["use_in_prototype"],
            "link": item["public_link"],
            "caveat": item["caveat"],
        })
    st.dataframe(pd.DataFrame(source_rows), use_container_width=True, hide_index=True)
    csv = master.to_csv(index=False).encode("utf-8")
    st.download_button("Download current processed CSV", csv, "gaia_storm_watch_processed.csv", "text/csv")

with tabs[3]:
    st.subheader("About this demonstrator")
    st.markdown(
        """
        GAIA Marine Storm Watch is an educational visualisation showing how public weather, coastal and metocean datasets can be cleaned, structured and presented as a clearer event story.  

        The prototype is intentionally conservative: it does not issue warnings, does not provide safety advice, and does not replace official sources. Its purpose is to demonstrate GAIA Marine's capability in marine data processing, dashboard development, metocean reporting and field-to-decision workflows.
        """
    )
    st.markdown("**Relevant GAIA Marine capability areas**")
    st.markdown("Metocean monitoring · Coastal data visualisation · Marine survey reporting · Automated QA/QC · Rapid event summaries · Client-ready dashboards")

footer_disclaimer()
