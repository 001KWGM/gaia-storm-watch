from __future__ import annotations

from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import yaml

from src.ui.components import caption

ROOT = Path(__file__).resolve().parents[2]


def load_camera_config() -> list[dict]:
    path = ROOT / "config" / "camera_links.yaml"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("coast_cams", [])


def camera_cards(cams: list[dict], selected_hub: str | None = None):
    if selected_hub and selected_hub != "All":
        cams = [c for c in cams if c.get("hub") == selected_hub]
    if not cams:
        st.info("No camera links configured for this hub.")
        return
    st.caption("Camera imagery is viewed at the official DTMI source pages. This public prototype does not copy, download, archive or rehost camera image files.")
    cols = st.columns(3)
    for i, cam in enumerate(cams):
        with cols[i % 3]:
            st.markdown(
                f"""
                <div class="gaia-card cam-card">
                    <h3>{cam.get('name')}</h3>
                    <p><b>Hub:</b> {cam.get('hub')}</p>
                    <p><b>Region:</b> {cam.get('region')}</p>
                    <p>{cam.get('view_note', '')}</p>
                    <p class="gaia-small"><b>Source:</b> {cam.get('source', 'WA Department of Transport and Major Infrastructure coast cam')}</p>
                    <p class="gaia-small"><b>Image timestamp:</b> shown on official source page where available.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.link_button("View official camera", cam.get("official_url", "#"))
            caption(f"Camera card: {cam.get('name')}. Source: {cam.get('source', 'WA Department of Transport and Major Infrastructure coast cam')}. Timestamp: official page timestamp where available. GAIA Marine links/previews the source page only and does not rehost the camera image.")


def official_camera_preview(cams: list[dict]):
    if not cams:
        st.info("No camera links configured.")
        return
    names = [c["name"] for c in cams]
    choice = st.selectbox("Official camera page preview", names)
    cam = next(c for c in cams if c["name"] == choice)
    st.markdown(
        "This preview attempts to embed the official DTMI camera page. If the page blocks embedding, use the official camera button instead. GAIA Marine is not copying or storing the camera image."
    )
    st.link_button("Open official camera in new tab", cam["official_url"])
    caption(f"Preview panel: {cam.get('name')}. Source: {cam.get('source', 'WA Department of Transport and Major Infrastructure coast cam')}. Image timestamp: shown on official source page where available. Preview is an official-page reference, not a GAIA-hosted image.")
    try:
        components.iframe(cam["official_url"], height=720, scrolling=True)
    except Exception:
        st.info("The official page could not be previewed here. Open it using the button above.")


def camera_source_note():
    st.markdown(
        """
        **Camera source handling**  
        GAIA Marine Storm Watch currently uses official camera links and optional official-page previews only. The app does not scrape, store, archive or republish the camera image files. This keeps the visual element useful while preserving source attribution and reducing copyright ambiguity.
        """
    )
