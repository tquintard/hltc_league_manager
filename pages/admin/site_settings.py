# ─────────────────────────────────────────────
# pages/admin/site_settings.py
# ─────────────────────────────────────────────

import streamlit as st
from modules.auth import require_role
from modules.ui import page_header
from modules.gsheets import reload_sheet
from config.settings import SHEET_SCHEMAS, APP_TITLE, APP_ICON

require_role("admin")
page_header("⚙️ Site Settings", "Application configuration and maintenance.")

# ── App info ──────────────────────────────────────────────────────────────────
st.subheader("📋 App info")
c1, c2, c3 = st.columns(3)
c1.metric("App", f"{APP_ICON} {APP_TITLE}")
c2.metric("Google Sheets tabs", len(SHEET_SCHEMAS))
c3.metric("Logged in as", st.session_state.get("display_name", "—"))

st.divider()

# ── Data overview ─────────────────────────────────────────────────────────────
st.subheader("🗃️ Sheet row counts")
cols = st.columns(len(SHEET_SCHEMAS))
for col, (name, _) in zip(cols, SHEET_SCHEMAS.items()):
    df  = st.session_state.dfs.get(name)
    cnt = len(df) if df is not None else 0
    col.metric(name.capitalize(), cnt)

st.divider()

# ── Force full reload ─────────────────────────────────────────────────────────
st.subheader("🔄 Force data reload")
st.caption("Reload all sheets from Google Sheets. Useful if data was edited directly in the sheet.")

if st.button("🔄 Reload all sheets", use_container_width=False):
    with st.spinner("Reloading…"):
        for name in SHEET_SCHEMAS:
            reload_sheet(name)
    st.success("All sheets reloaded.")

st.divider()

# ── Secrets check ─────────────────────────────────────────────────────────────
st.subheader("🔑 Secrets configuration")

if "gsheets" in st.secrets:
    st.success("✅ `secrets.toml` is configured — captain/player login is available.")
    try:
        url = st.secrets["gsheets"]["url"]
        st.caption(f"Connected sheet: `{url}`")
    except KeyError:
        st.warning("Found `[gsheets]` section but `url` key is missing.")
else:
    st.error(
        "❌ `[gsheets]` section not found in `secrets.toml`.  \n"
        "Captain and player login will not work until you configure it.  \n\n"
        "See `.streamlit/secrets.toml.example` for the required format."
    )
