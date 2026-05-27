from __future__ import annotations

import pandas as pd
import streamlit as st

from src.process.build_master import build_demo_master
from src.process.analytics import hub_snapshot, event_digest_markdown
from src.ui.branding import css, GAIA_DARK, GAIA_GOLD, GAIA_GREY
from src.ui.components import hero, caption, latest_display_time, source_mode_text, fmt_time
from src.ui.disclaimers import top_disclaimer, footer_disclaimer
from src.ui.lead_capture import registration_gate
from src.ui.weather_references import load_weather_references, contact_panel
from src.ui.cameras import load_camera_config, camera_source_note
from src.utils.config import load_hubs, load_sources, load_yaml
from src.ui.simple_view import (
    cap_to_latest_available,
    render_time_slider,
    render_snapshot_cards,
    render_location_stats,
    render_simple_timeline,
    render_all_locations_table,
    render_weather_reference_strip,
    render_camera_strip,
    render_source_expanders,
)

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
CONTACT_EMAIL = public_cfg.get("contact_email", "info@gaia-marine.com.au")
WEBSITE_URL = public_cfg.get("website_url", "https://gaia-marine.com.au")

hero(EVENT["public_name"], EVENT["subtitle"])
top_disclaimer()
registration_gate(EVENT["public_name"], app_cfg)

@st.cache_data(show_spinner=False)
def get_curated_master():
    return build_demo_master()

master = get_curated_master()
master = cap_to_latest_available(master, public_cfg)

if master.empty:
    st.warning(
        "No displayed records are currently available. GAIA Marine controls the published dataset internally; "
        "records will appear here once the event display dataset has been updated."
    )
    footer_disclaimer()
    st.stop()

last_display = pd.to_datetime(master["timestamp_awst"], errors="coerce").max()
first_display = pd.to_datetime(master["timestamp_awst"], errors="coerce").min()

st.markdown(
    f"""
    <div class="story-panel">
        <h3>One-screen storm viewer</h3>
        <p>This simplified version shows one timestamp at a time. Use the time bar once, then read the map, weather references, coast camera links, and summary stats for the selected location.</p>
        <p><b>Displayed period:</b> {first_display.strftime('%d %b %Y %H:%M AWST')} to {last_display.strftime('%d %b %Y %H:%M AWST')} · <b>Future observations are not shown.</b></p>
    </div>
    """,
    unsafe_allow_html=True,
)

# The only public controls: location and timestamp.
hub_names = list(HUBS.keys())
default_hub = public_cfg.get("default_hub", "Perth")
default_idx = hub_names.index(default_hub) if default_hub in hub_names else 0
c_loc, c_time = st.columns([0.34, 0.66])
with c_loc:
    selected_hub = st.selectbox("Location", hub_names, index=default_idx)
with c_time:
    selected_time = render_time_slider(master, public_cfg)

hub_label = HUBS.get(selected_hub, {}).get("display_name", selected_hub)
st.markdown(f"## {hub_label} · {selected_time.strftime('%d %b %Y %H:%M AWST')}")
st.caption("All dashboard timestamps are displayed in AWST. External official pages may use their own issue, observation or validity timestamps.")

snapshot_all = master[master["timestamp_awst"].eq(selected_time)].copy()
if snapshot_all.empty:
    # Robust fallback to nearest records per hub.
    rows = []
    for hub, g in master.groupby("hub"):
        g = g.copy()
        idx = (g["timestamp_awst"] - selected_time).abs().idxmin()
        rows.append(g.loc[idx])
    snapshot_all = pd.DataFrame(rows)

selected_snapshot = snapshot_all[snapshot_all["hub"].eq(selected_hub)]
if selected_snapshot.empty:
    selected_snapshot = snapshot_all.head(1)

# Row 1: map + selected-time cards.
map_col, card_col = st.columns([0.44, 0.56])
with map_col:
    st.markdown("### Location overview")
    map_df = pd.DataFrame([
        {"hub": h, "display_name": m["display_name"], "lat": m["lat"], "lon": m["lon"], "selected": h == selected_hub}
        for h, m in HUBS.items()
    ])
    # Streamlit map does not support per-point custom styling reliably; keep it simple.
    st.map(map_df.rename(columns={"lat": "latitude", "lon": "longitude"}), latitude="latitude", longitude="longitude", size=90, color="#E4C21C")
    caption("Map: configured WA coastal locations included in the GAIA Marine Storm Watch public display. Source: GAIA Marine dashboard configuration. Timestamp: static location layer; not time-varying weather data.")
with card_col:
    st.markdown("### Selected-time conditions")
    render_snapshot_cards(selected_snapshot.iloc[0], selected_time)

# Row 2: official weather references and surf cameras.
weather_col, cam_col = st.columns([0.50, 0.50])
with weather_col:
    st.markdown("### Official weather context")
    render_weather_reference_strip(WEATHER_REFS)
with cam_col:
    st.markdown("### Coast camera context")
    render_camera_strip(CAMS, selected_hub)

# Row 3: simple chart and stats.
st.markdown("### Displayed trend to latest available record")
hub_df = master[master["hub"].eq(selected_hub)].copy()
st.plotly_chart(render_simple_timeline(hub_df, hub_label, selected_time), use_container_width=True)
caption(f"Graph: simplified observed/displayed trend for {hub_label}, capped at the latest available dashboard record. Source mode: {source_mode_text(hub_df)}. Latest displayed timestamp: {latest_display_time(hub_df)}. This is a general-interest visual summary, not official forecast, warning, safety or commercial decision advice.")

st.markdown("### Location summary")
render_location_stats(hub_df, selected_hub, hub_label)

st.markdown("### Same timestamp across locations")
render_all_locations_table(snapshot_all)
caption(f"Table: all configured coastal locations at the selected dashboard timestamp. Source mode: {source_mode_text(master)}. Selected timestamp: {selected_time.strftime('%d %b %Y %H:%M AWST')}. Missing or unavailable values are shown transparently.")

# Summary and transparency, but not as a maze of buttons.
st.markdown("### Event summary")
st.markdown(event_digest_markdown(master, EVENT["public_name"]))
caption(f"Summary: automatically generated public-interest digest from the curated displayed dataset. Latest displayed timestamp: {latest_display_time(master)}. Future observations are not displayed.")

render_source_expanders(master, sources, WEATHER_REFS, CAMS)
contact_panel(CONTACT_EMAIL, WEBSITE_URL)
footer_disclaimer()
