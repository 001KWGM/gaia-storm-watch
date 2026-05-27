from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st
import yaml

from src.ui.components import caption


def load_weather_references() -> list[dict]:
    p = Path("config/weather_references.yaml")
    if not p.exists():
        return []
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return data.get("weather_references", [])


def weather_reference_board(refs: list[dict], event: dict):
    st.subheader("Weather maps, radar and synoptic references")
    st.markdown(
        "These official reference links provide broader visual context for the weather system: radar, warnings, synoptic/isobar charts and satellite imagery. They are linked as source references rather than copied, archived or rehosted by GAIA Marine."
    )
    st.info(
        "Time alignment rule: dashboard plots are displayed in AWST. External radar, satellite and weather-map pages show their own issue, validity or observation timestamps; those source timestamps should be used when comparing the visual reference to the dashboard timeline."
    )

    if not refs:
        st.warning("No weather-map references configured.")
        return

    cols = st.columns(3)
    for i, item in enumerate(refs):
        with cols[i % 3]:
            st.markdown(
                f"""
                <div class="gaia-card">
                    <h3>{item.get('name','Reference')}</h3>
                    <p><b>{item.get('type','Reference')}</b></p>
                    <p>{item.get('role','')}</p>
                    <p class="gaia-small"><b>Source timestamp:</b> {item.get('time_alignment','Shown on official source page where available')}</p>
                    <p class="gaia-small"><b>Source:</b> {item.get('source','Official external source')}</p>
                    <p class="gaia-small">{item.get('caveat','')}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.link_button("Open official source", item.get("url", "https://www.bom.gov.au/"))
            caption(f"Reference card: {item.get('name','Reference')}. Source: {item.get('source','official external source')}. Timestamp/validity: displayed on the official source page where available. GAIA Marine does not rehost the image/map product.")

    with st.expander("Reference register", expanded=False):
        st.dataframe(pd.DataFrame(refs), use_container_width=True, hide_index=True)
        caption("Weather-reference register controlled by GAIA Marine configuration. These are official external references for context only, not reproduced weather products.")


def contact_panel(contact_email: str, website_url: str):
    st.markdown("### Get in touch with GAIA Marine")
    st.markdown(
        "For marine data dashboards, metocean monitoring, coastal survey reporting or event-based visual summaries, contact GAIA Marine."
    )
    c1, c2 = st.columns(2)
    c1.link_button("Email GAIA Marine", f"mailto:{contact_email}?subject=GAIA%20Marine%20Storm%20Watch%20enquiry")
    c2.link_button("Visit GAIA Marine website", website_url)
