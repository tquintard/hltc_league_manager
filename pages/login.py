# ─────────────────────────────────────────────
# pages/login.py — Login screen
# ─────────────────────────────────────────────

import streamlit as st
from modules.auth import try_login_with_password, try_login_as_admin
from modules.ui import require_gsheets_secrets


def show_login() -> None:
    st.title("🎾 Tennis Club")
    st.caption("Match management & availability portal")
    st.divider()

    tab_admin, tab_user = st.tabs(["🔐 Site Admin", "🎾 Captain / Player"])

    # ── Admin tab ───────────────────────────────────────────────────────────
    with tab_admin:
        st.subheader("Admin – Connect via Google Sheets")
        st.info(
            "The site admin authenticates directly with Google Sheets credentials. "
            "This is used for first-time setup and account management."
        )

        with st.expander("📖 How to configure Google Sheets access"):
            st.markdown(
                "1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a project.\n"
                "2. Enable **Google Sheets API** and **Google Drive API**.\n"
                "3. Under *IAM & Admin > Service Accounts*, create a service account "
                "and download a **JSON key**.\n"
                "4. Create a Google Sheets file and **share it** with the service account "
                "email (Editor role).\n"
                "5. The app will auto-create all required tabs on first connection.\n"
                "6. Paste the JSON and URL below."
            )

        with st.form("admin_login_form"):
            creds_raw = st.text_area(
                "Service account JSON credentials",
                height=150,
                placeholder='{"type": "service_account", "project_id": "...", ...}',
            )
            sheet_url = st.text_input(
                "Google Sheets URL",
                placeholder="https://docs.google.com/spreadsheets/d/XXXXX/edit",
            )
            submitted = st.form_submit_button("🔌 Connect as Admin", use_container_width=True)

        if submitted:
            if not creds_raw.strip() or not sheet_url.strip():
                st.error("Please fill in both fields.")
            else:
                with st.spinner("Connecting to Google Sheets…"):
                    ok, err = try_login_as_admin(creds_raw.strip(), sheet_url.strip())
                if ok:
                    st.success("Connected! Welcome, Admin.")
                    st.rerun()
                else:
                    st.error(err)

        st.divider()
        st.caption(
            "💡 **First-time setup?** After connecting, an `admin` account is automatically "
            "created in your Google Sheets with the default password `changeme`. "
            "Go to *Admin → Manage Accounts* to change it."
        )

    # ── Captain / Player tab ────────────────────────────────────────────────
    with tab_user:
        st.subheader("Captain / Player – Sign in")

        secrets_ok = require_gsheets_secrets()
        if not secrets_ok:
            st.stop()

        with st.form("user_login_form"):
            pseudo   = st.text_input("Username", placeholder="Your pseudo")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("🎾 Sign in", use_container_width=True)

        if submitted:
            if not pseudo.strip() or not password.strip():
                st.error("Please enter your username and password.")
            else:
                with st.spinner("Signing in…"):
                    ok, err = try_login_with_password(pseudo.strip(), password.strip())
                if ok:
                    st.success(f"Welcome, {pseudo}!")
                    st.rerun()
                else:
                    st.error(err)

        st.caption("Don't have an account? Ask your site admin to create one for you.")
