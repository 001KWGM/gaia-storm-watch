from __future__ import annotations

import pandas as pd
import streamlit as st

from src.process.build_master import build_demo_master, normalize_uploaded_file, save_master
from src.process.analytics import coverage_summary, hub_snapshot, threshold_events, event_digest_markdown
from src.ui.branding import css
from src.ui.components import hero, kpi_cards, source_status_table, narrative_summary, insight_cards, interest_form
from src.ui.charts import storm_timeline, compare_hubs, peak_timing_strip, event_phase_ribbon, coverage_heatmap
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
    st.header("Data controls")
    st.caption("For public release, replace demo data with checked public-source CSVs and keep the source transparency tab visible.")
    use_demo = st.toggle("Use synthetic demo data", value=True)
    fallback_hub = st.selectbox("Fallback hub for uploaded files", ["Perth", "Geraldton", "Bunbury", "Albany", "Uploaded"], index=0)
    uploads = st.file_uploader(
        "Optional CSV upload(s)", type=["csv"], accept_multiple_files=True,
        help="Flexible columns accepted: timestamp/date/time, hub/site/station, hs/Hm0, wind gust, rain, pressure, tide/water level, residual/anomaly etc."
    )
    st.markdown("---")
    st.caption("Official information should be read at source.")
    st.link_button("BOM WA warnings", "https://www.bom.gov.au/wa/warnings/")
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
            frames.append(normalize_uploaded_file(f, fallback_hub=fallback_hub))
        except Exception as exc:
            errors.append(f"{f.name}: {exc}")

if not frames:
    st.warning("No data selected. Turn on demo data or upload one or more CSV files.")
    st.stop()

master = pd.concat(frames, ignore_index=True)
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
    st.info("Prototype is currently showing synthetic demonstration data. Replace with checked public-source data before external publication.")

# Core derived products
snapshot = hub_snapshot(master)
coverage = coverage_summary(master)
events = threshold_events(master)
digest_md = event_digest_markdown(master, EVENT["public_name"])

# Top-level story block
st.subheader("Event snapshot")
kpi_cards(master)
insight_cards(snapshot)

left, right = st.columns([1.05, 1])
with left:
    st.markdown("### Coastal hubs")
    map_df = pd.DataFrame([
        {"hub": h, "display_name": m["display_name"], "lat": m["lat"], "lon": m["lon"], "region": m["region"]}
        for h, m in HUBS.items()
    ])
    st.map(map_df.rename(columns={"lat": "latitude", "lon": "longitude"}), latitude="latitude", longitude="longitude", size=90, color="#E4C21C")
with right:
    st.markdown("### Event-shape overview")
    st.plotly_chart(event_phase_ribbon(master), use_container_width=True)

tabs = st.tabs(["Overview", "Storm timeline", "Coastal hubs", "Data QA", "Event digest", "About"])

with tabs[0]:
    st.subheader("General-interest overview")
    st.markdown(
        "This view is intended to show how public weather, coastal and metocean data can be combined into a readable event story. It is deliberately not framed as a warning tool, marine-safety tool or authority dashboard."
    )
    st.dataframe(snapshot, use_container_width=True, hide_index=True)
    st.markdown("### Official source links")
    c1, c2, c3 = st.columns(3)
    c1.link_button("BOM WA warnings", "https://www.bom.gov.au/wa/warnings/")
    c2.link_button("Emergency WA", "https://www.emergency.wa.gov.au/")
    c3.link_button("WA coastal data", "https://www.transport.wa.gov.au/marine/coastal-data-charts.asp")

with tabs[1]:
    st.subheader("Storm timeline")
    hub = st.selectbox("Select coastal hub", sorted(master["hub"].dropna().unique()), key="timeline_hub")
    hub_label = HUBS.get(hub, {}).get("display_name", hub)
    g = master[master["hub"] == hub]
    narrative_summary(g, hub_label)
    st.plotly_chart(storm_timeline(g, hub_label), use_container_width=True)

with tabs[2]:
    st.subheader("Coastal hub comparison")
    metric_options = {
        "Significant wave height Hs (m)": "wave_hs_m",
        "Maximum wave height Hmax (m)": "wave_hmax_m",
        "Wind gust (km/h)": "wind_gust_kmh",
        "Rainfall per interval (mm)": "rainfall_mm",
        "Water-level residual indicator (m)": "water_level_residual_m",
    }
    selected_label = st.selectbox("Metric", list(metric_options.keys()))
    selected_metric = metric_options[selected_label]
    st.plotly_chart(compare_hubs(master, selected_metric, selected_label), use_container_width=True)
    st.plotly_chart(peak_timing_strip(master), use_container_width=True)
    st.markdown("### General-interest indicator counts")
    st.caption("These are display indicators only. They are not official warning or safety thresholds.")
    st.dataframe(events, use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("Data QA and transparency")
    st.markdown("This tab stays visible by design. It makes the dashboard more credible by showing source mode, coverage and caveats.")
    source_status_table(master)
    st.plotly_chart(coverage_heatmap(coverage), use_container_width=True)
    st.dataframe(coverage, use_container_width=True, hide_index=True)
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

with tabs[4]:
    st.subheader("Post-event digest")
    st.markdown("The digest is designed as a concise public summary once observed data have been checked.")
    st.markdown(digest_md)
    st.download_button("Download digest as Markdown", digest_md.encode("utf-8"), "gaia_storm_watch_event_digest.md", "text/markdown")
    interest_form()

with tabs[5]:
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
