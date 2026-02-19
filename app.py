# ─────────────────────────────────────────────
# app.py — Entry point & dynamic navigation
# ─────────────────────────────────────────────

import streamlit as st
from config.settings import APP_TITLE, APP_ICON
from modules.auth import init_session_state

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()

# ── Not authenticated → show login ─────────────────────────────────────────
if not st.session_state.authenticated:
    from pages.login import show_login
    show_login()
    st.stop()

# ── Build page list based on roles ─────────────────────────────────────────
from modules.auth import has_role

pages: dict[str, list[st.Page]] = {}

# Player section — available to all authenticated users
pages["🎾 Player"] = [
    st.Page("pages/player/calendar.py",      title="Match Calendar",  icon="📅"),
    st.Page("pages/player/availability.py",  title="My Availability", icon="🗳️"),
    st.Page("pages/player/results.py",       title="Results",         icon="🏆"),
    st.Page("pages/player/selections.py",    title="Selections",      icon="👥"),
]

# Captain section
if has_role("captain", "admin"):
    pages["⚓ Captain"] = [
        st.Page("pages/captain/dashboard.py",            title="Dashboard",            icon="📊"),
        st.Page("pages/captain/create_match.py",         title="Create Match",         icon="➕"),
        st.Page("pages/captain/enter_results.py",        title="Enter Results",        icon="📝"),
        st.Page("pages/captain/availability_manager.py", title="Availability Manager", icon="🗳️"),
        st.Page("pages/captain/statistics.py",           title="Statistics",           icon="📈"),
    ]

# Admin section
if has_role("admin"):
    pages["🔐 Admin"] = [
        st.Page("pages/admin/manage_accounts.py", title="Manage Accounts", icon="👤"),
        st.Page("pages/admin/site_settings.py",   title="Site Settings",   icon="⚙️"),
    ]

# Run navigation
pg = st.navigation(pages)

# Sidebar footer (logout, refresh, user info) — shown on every page
from modules.ui import render_sidebar_footer
render_sidebar_footer()

pg.run()
