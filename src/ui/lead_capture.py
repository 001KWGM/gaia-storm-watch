from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class SaveResult:
    ok: bool
    mode: str
    message: str


def _now_awst() -> str:
    return datetime.now(ZoneInfo("Australia/Perth")).strftime("%Y-%m-%d %H:%M:%S AWST")


def _local_save(row: dict) -> SaveResult:
    out = Path("data/processed/registrations_local_fallback.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    exists = out.exists()
    with out.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    return SaveResult(True, "local_csv", "Registration stored in local fallback CSV.")


def _gspread_save(row: dict, sheet_name: str) -> SaveResult:
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except Exception as exc:
        return SaveResult(False, "google_sheets", f"Google Sheets libraries unavailable: {exc}")

    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        if "gcp_service_account" not in st.secrets:
            return SaveResult(False, "google_sheets", "Missing gcp_service_account in Streamlit secrets.")
        if "registration" not in st.secrets or "spreadsheet_url" not in st.secrets["registration"]:
            return SaveResult(False, "google_sheets", "Missing registration.spreadsheet_url in Streamlit secrets.")

        creds_info = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_url(st.secrets["registration"]["spreadsheet_url"])
        try:
            ws = sh.worksheet(sheet_name)
        except Exception:
            ws = sh.add_worksheet(title=sheet_name, rows=1000, cols=len(row) + 2)
        existing = ws.get_all_values()
        headers = list(row.keys())
        if not existing:
            ws.append_row(headers)
        elif existing[0] != headers:
            missing = [h for h in headers if h not in existing[0]]
            if missing:
                ws.append_row(["HEADER_MISMATCH", "Missing columns in sheet", ", ".join(missing)])
        ws.append_row([row.get(h, "") for h in headers], value_input_option="USER_ENTERED")
        return SaveResult(True, "google_sheets", "Registration stored in Google Sheets.")
    except Exception as exc:
        return SaveResult(False, "google_sheets", f"Google Sheets save failed: {exc}")


def save_registration(row: dict, sheet_name: str) -> SaveResult:
    gs = _gspread_save(row, sheet_name)
    if gs.ok:
        return gs
    fallback = _local_save(row)
    if fallback.ok:
        return SaveResult(True, "local_csv_fallback", f"{fallback.message} Google Sheets issue: {gs.message}")
    return SaveResult(False, "failed", gs.message)


def registration_gate(event_name: str, app_cfg: dict) -> bool:
    public_cfg = app_cfg.get("public_app", {})
    if not public_cfg.get("require_registration", False):
        return True
    if st.session_state.get("registered_for_storm_watch", False):
        return True

    contact_email = public_cfg.get("contact_email", "solutions@gaia-marine.ai")
    website_url = public_cfg.get("website_url", "https://gaia-marine.com.au")
    sheet_name = public_cfg.get("registration_sheet_name", "Registrations")

    st.markdown(
        """
        <div class="story-panel">
            <h3>Register to view GAIA Marine Storm Watch</h3>
            <p>This public visualiser is provided for general interest and brand awareness. Registration helps GAIA Marine understand who is accessing the demonstrator and follow up with people interested in marine data, metocean monitoring and digital reporting.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="gaia-legal">
        <b>Privacy collection notice.</b> GAIA Marine collects your name, organisation and email address to provide access to this demonstrator, record public interest in the dashboard and contact you about GAIA Marine services where consent is provided below. Your details are stored in GAIA Marine controlled records and are not intended for public display. You can request removal or unsubscribe from future contact by emailing GAIA Marine.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("storm_watch_registration"):
        c1, c2 = st.columns(2)
        first_name = c1.text_input("First name *")
        last_name = c2.text_input("Last name *")
        company = st.text_input("Company / organisation")
        email = st.text_input("Email address *")
        acknowledgement = st.checkbox(
            "I understand this dashboard is for general interest only and is not official emergency, forecast, marine safety, operational or commercial decision advice. *"
        )
        marketing_consent = st.checkbox(
            "I agree to GAIA Marine contacting me about this demonstrator and related marine data, metocean, survey and reporting services. I can unsubscribe at any time. *"
        )
        submitted = st.form_submit_button("Enter dashboard", type="primary")

    st.caption(f"Contact: {contact_email} · Website: {website_url}")

    if not submitted:
        st.stop()

    errors = []
    if not first_name.strip():
        errors.append("First name is required.")
    if not last_name.strip():
        errors.append("Last name is required.")
    if not email.strip() or not EMAIL_RE.match(email.strip()):
        errors.append("A valid email address is required.")
    if not acknowledgement:
        errors.append("Please acknowledge the dashboard limitation statement.")
    if not marketing_consent:
        errors.append("Please provide contact consent to access this public demonstrator.")

    if errors:
        for e in errors:
            st.error(e)
        st.stop()

    row = {
        "timestamp_awst": _now_awst(),
        "event": event_name,
        "first_name": first_name.strip(),
        "last_name": last_name.strip(),
        "company": company.strip(),
        "email": email.strip().lower(),
        "acknowledged_general_interest_only": "yes",
        "marketing_contact_consent": "yes",
        "source": "streamlit_public_dashboard",
    }
    result = save_registration(row, sheet_name)
    if not result.ok:
        st.error("Registration could not be saved. Please try again or contact GAIA Marine.")
        st.stop()

    st.session_state["registered_for_storm_watch"] = True
    st.session_state["registered_email"] = email.strip().lower()
    st.rerun()

    return False
