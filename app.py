from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ingest.fetch_open_meteo import fetch_weather_for_hubs, blend_weather_into_master
from src.process.build_master import build_demo_master
from src.process.analytics import coverage_summary, hub_snapshot, threshold_events, event_digest_markdown
from src.ui.branding import css
from src.ui.components import (
    hero,
    kpi_cards,
    source_status_table,
    narrative_summary,
    insight_cards,
    storm_story_panel,
    quick_story_tiles,
    caption,
    latest_display_time,
    source_mode_text,
)
from src.ui.charts import storm_timeline, compare_hubs, peak_timing_strip, event_phase_ribbon, coverage_heatmap
from src.ui.cameras import load_camera_config, camera_cards, official_camera_preview, camera_source_note
from src.ui.disclaimers import top_disclaimer, footer_disclaimer
from src.ui.lead_capture import registration_gate
from src.ui.weather_references import load_weather_references, weather_reference_board, contact_panel
from src.utils.config import load_hubs, load_sources, load_yaml

st.set_page_config(
    page_title="GAIA Marine Storm Watch",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(css(), unsafe_allow_html=True)

cfg = load_hubs()
sources = load_sources()
app_cfg = load_yaml("app_config.yaml")
public_cfg = app_cfg.get("public_app", {})
EVENT = cfg["event"]
HUBS = cfg["hubs"]
CAMS = load_camera_config()
WEATHER_REFS = load_weather_references()

hero(EVENT["public_name"], EVENT["subtitle"])
top_disclaimer()
registration_gate(EVENT["public_name"], app_cfg)

# Public-display rule: public users do not control ingestion, thresholds, source mode,
# uploads, processing settings or QA/QC parameters. GAIA controls those internally via
# config files and processed datasets. Public interaction is limited to curated viewing.
DATA_MODE_LABEL = public_cfg.get("public_data_mode_label", "Curated public display")
AUTO_WEATHER_ENABLED = bool(public_cfg.get("enable_auto_weather_context", True))
CAMERA_PREVIEW_ENABLED = bool(public_cfg.get("enable_official_camera_page_preview", True))
SHOW_DIGEST_DOWNLOAD = bool(public_cfg.get("show_public_digest_download", True))
WEATHER_REFERENCE_ENABLED = bool(public_cfg.get("enable_weather_reference_board", True))
CONTACT_EMAIL = public_cfg.get("contact_email", "info@gaia-marine.com.au")
WEBSITE_URL = public_cfg.get("website_url", "https://gaia-marine.com.au")

@st.cache_data(show_spinner=False)
def get_demo():
    return build_demo_master()

@st.cache_data(show_spinner=True, ttl=1800)
def get_auto_weather(hubs: dict):
    return fetch_weather_for_hubs(hubs)

master = get_demo()
auto_weather_errors: list[str] = []

if AUTO_WEATHER_ENABLED:
    result = get_auto_weather(HUBS)
    auto_weather_errors = result.errors
    if not result.data.empty:
        master = blend_weather_into_master(master, result.data)

master["timestamp_awst"] = pd.to_datetime(master["timestamp_awst"], errors="coerce")
master = master.dropna(subset=["timestamp_awst"]).sort_values(["hub", "timestamp_awst"])

source_modes = sorted(master["source_mode"].dropna().astype(str).unique())
if auto_weather_errors:
    st.info("Some live weather-context requests were unavailable, so the display retains the curated demonstration context where needed.")
elif AUTO_WEATHER_ENABLED and any("Auto weather" in s for s in source_modes):
    st.info("Weather context is auto-refreshed by the app. Marine and water-level context remains a curated demonstration layer until checked public-source feeds are connected.")
else:
    st.info("This public display is currently using a curated demonstration dataset. Source choices and processing settings are controlled internally by GAIA Marine.")

snapshot = hub_snapshot(master)
coverage = coverage_summary(master)
events = threshold_events(master)
digest_md = event_digest_markdown(master, EVENT["public_name"])

storm_story_panel(EVENT["public_name"], DATA_MODE_LABEL)
quick_story_tiles(master)

left, right = st.columns([1.05, 1])
with left:
    st.markdown("### WA coastal hubs")
    map_df = pd.DataFrame([
        {"hub": h, "display_name": m["display_name"], "lat": m["lat"], "lon": m["lon"], "region": m["region"]}
        for h, m in HUBS.items()
    ])
    st.map(map_df.rename(columns={"lat": "latitude", "lon": "longitude"}), latitude="latitude", longitude="longitude", size=90, color="#E4C21C")
    caption("Map: configured WA coastal hub locations used by GAIA Marine Storm Watch. Source: GAIA Marine dashboard configuration. Timestamp: static hub-location layer, not time-varying storm data.")
with right:
    st.markdown("### Event-shape overview")
    st.plotly_chart(event_phase_ribbon(master), use_container_width=True)
    caption(f"Graph: relative event-shape overview generated from the curated displayed dataset. Source mode: {source_mode_text(master)}. Latest displayed timestamp: {latest_display_time(master)}. This is a storytelling index, not an official severity scale.")

tabs = st.tabs(["Storm story", "Timeline", "Weather maps", "Coast cams", "Coastal hubs", "Sources", "Digest", "About"])

with tabs[0]:
    st.subheader("Approaching storm · during event · aftermath")
    st.markdown(
        """
        This page is the plain-English story layer. It is designed as a public-interest visual summary of how a coastal storm can build, peak and ease across Western Australia. It is deliberately not a technical analysis tool and is not intended for marine operations, emergency response or safety decisions.
        """
    )
    kpi_cards(master)
    insight_cards(snapshot)
    st.markdown("### Official information")
    c1, c2, c3, c4 = st.columns(4)
    c1.link_button("BOM WA warnings", "https://www.bom.gov.au/wa/warnings/")
    c2.link_button("Emergency WA", "https://www.emergency.wa.gov.au/")
    c3.link_button("WA coastal data", "https://www.transport.wa.gov.au/marine/coastal-data-charts.asp")
    c4.link_button("WA coast cams", "https://www.transport.wa.gov.au/marine/charts-warnings-current-conditions/coast-cams")
    st.markdown("---")
    contact_panel(CONTACT_EMAIL, WEBSITE_URL)

with tabs[1]:
    st.subheader("Storm timeline")
    hub_names = sorted(master["hub"].dropna().unique())
    default_hub = public_cfg.get("default_hub", "Perth")
    default_idx = hub_names.index(default_hub) if default_hub in hub_names else 0
    hub = st.selectbox("Select coastal hub", hub_names, index=default_idx, key="timeline_hub")
    hub_label = HUBS.get(hub, {}).get("display_name", hub)
    g = master[master["hub"] == hub]
    narrative_summary(g, hub_label)
    st.plotly_chart(storm_timeline(g, hub_label), use_container_width=True)
    caption(f"Graph: storm timeline for {hub_label}. Source mode: {source_mode_text(g)}. Latest displayed timestamp: {latest_display_time(g)}. All dashboard timestamps are shown in AWST. Values are for public-interest visualisation only.")

with tabs[2]:
    if WEATHER_REFERENCE_ENABLED:
        weather_reference_board(WEATHER_REFS, EVENT)
    else:
        st.info("Weather-map reference board is disabled in the current public configuration.")

with tabs[3]:
    st.subheader("Official coast camera views")
    st.markdown(
        "The camera layer is handled through official source links and optional official-page previews. GAIA Marine does not archive or rehost third-party camera images in this public prototype."
    )
    hub_filter = st.selectbox("Select camera region", ["All", "Perth", "Geraldton", "Bunbury", "Albany"], index=0)
    camera_cards(CAMS, selected_hub=hub_filter)
    if CAMERA_PREVIEW_ENABLED:
        with st.expander("Preview an official camera page", expanded=True):
            official_camera_preview(CAMS)
    camera_source_note()

with tabs[4]:
    st.subheader("Coastal hub comparison")
    metric_options = {
        "Significant wave height Hs (m)": "wave_hs_m",
        "Maximum wave height Hmax (m)": "wave_hmax_m",
        "Wind gust (km/h)": "wind_gust_kmh",
        "Rainfall per interval (mm)": "rainfall_mm",
        "Water-level residual indicator (m)": "water_level_residual_m",
    }
    metric_labels = list(metric_options.keys())
    default_metric = public_cfg.get("default_compare_metric", "wave_hs_m")
    default_label = next((k for k, v in metric_options.items() if v == default_metric), metric_labels[0])
    selected_label = st.selectbox("Select displayed metric", metric_labels, index=metric_labels.index(default_label))
    selected_metric = metric_options[selected_label]
    st.plotly_chart(compare_hubs(master, selected_metric, selected_label), use_container_width=True)
    caption(f"Graph: comparison of highest displayed {selected_label} by coastal hub. Source mode: {source_mode_text(master)}. Latest displayed timestamp: {latest_display_time(master)}.")
    st.plotly_chart(peak_timing_strip(master), use_container_width=True)
    caption(f"Graph: timing of highest displayed values by hub and selected indicators. Source mode: {source_mode_text(master)}. Latest displayed timestamp: {latest_display_time(master)}.")
    st.markdown("### General-interest event markers")
    st.caption("These are display indicators only. They are not official warning, safety or operational thresholds.")
    st.dataframe(events, use_container_width=True, hide_index=True)
    caption("Table: general-interest event markers derived from the curated displayed dataset and internally configured display thresholds. These are not official warning, safety, operational or commercial-decision thresholds.")

with tabs[5]:
    st.subheader("Sources and transparency")
    st.markdown(
        "This dashboard is intentionally transparent about where information comes from and how it should be read. Public users cannot change source choices, thresholds or processing settings."
    )
    source_status_table(master)
    st.plotly_chart(coverage_heatmap(coverage), use_container_width=True)
    caption(f"Graph: displayed data coverage by hub and dataset. Source mode: {source_mode_text(master)}. Latest displayed timestamp: {latest_display_time(master)}.")
    with st.expander("Source register", expanded=False):
        source_rows = []
        for key, item in sources["sources"].items():
            source_rows.append({
                "source": item["display_name"],
                "prototype_use": item["use_in_prototype"],
                "link": item["public_link"],
                "caveat": item["caveat"],
            })
        st.dataframe(pd.DataFrame(source_rows), use_container_width=True, hide_index=True)
        caption("Table: source register controlled by GAIA Marine configuration. External information remains subject to the relevant source agency terms, copyright, disclaimers and conditions of use.")

with tabs[6]:
    st.subheader("Post-event digest")
    st.markdown("The digest is a concise public summary prepared from the curated displayed dataset. It is intended for general interest and capability demonstration.")
    st.markdown(digest_md)
    caption(f"Text summary: public digest generated from the curated displayed dataset. Source mode: {source_mode_text(master)}. Latest displayed timestamp: {latest_display_time(master)}.")
    if SHOW_DIGEST_DOWNLOAD:
        st.download_button("Download public digest", digest_md.encode("utf-8"), "gaia_storm_watch_public_digest.md", "text/markdown")

with tabs[7]:
    st.subheader("About this demonstrator")
    st.markdown(
        """
        GAIA Marine Storm Watch is a public-facing event visualiser showing how weather, coastal and metocean information can be curated into a clearer story for general interest, aligned with GAIA Marine’s data-driven marine survey and engineering positioning.

        The public dashboard is intentionally simple: viewers can select what they want to look at, but all source choices, processing settings, thresholds, data updates and interpretation boundaries are controlled internally by GAIA Marine. This keeps the app clean, controlled and legally conservative.

        The prototype does not issue warnings, does not provide safety advice and does not replace official information sources.
        """
    )
    st.markdown("**Relevant GAIA Marine capability areas**")
    st.markdown("Metocean monitoring · Coastal data visualisation · Marine survey reporting · Automated QA/QC · Rapid event summaries · Client-ready dashboards")
    st.markdown("---")
    contact_panel(CONTACT_EMAIL, WEBSITE_URL)

footer_disclaimer()
