# ─────────────────────────────────────────────
# modules/ui.py — Reusable UI components
# ─────────────────────────────────────────────

from __future__ import annotations

import streamlit as st
import pandas as pd
from modules.auth import logout, has_role


def render_sidebar_footer() -> None:
    """Render logout button and user info at the bottom of the sidebar."""
    st.sidebar.divider()
    pseudo       = st.session_state.get("display_name") or st.session_state.get("pseudo", "")
    roles        = st.session_state.get("roles", [])
    roles_str    = " · ".join(r.capitalize() for r in roles)
    st.sidebar.caption(f"👤 **{pseudo}**  \n_{roles_str}_")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            from modules.gsheets import reload_sheet
            from config.settings import SHEET_SCHEMAS
            for k in SHEET_SCHEMAS:
                reload_sheet(k)
            st.rerun()
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            logout()


def page_header(title: str, subtitle: str = "") -> None:
    """Render a consistent page title + optional caption + divider."""
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    st.divider()


def match_card(row: pd.Series, extra: dict | None = None) -> None:
    """
    Render an upcoming or played match inside a bordered container.
    extra: optional dict of label→value pairs to show on the right.
    """
    with st.container(border=True):
        left, right = st.columns([4, 2])
        with left:
            date_str = row["date"].strftime("%d %b %Y") if pd.notna(row.get("date")) else "—"
            st.write(f"**{date_str}** — vs **{row.get('opponent_club', '—')}**")
            st.caption(
                f"{row.get('competition_type', '')}  ·  {row.get('team', '')}  ·  "
                f"📍 {row.get('location', '—')}"
            )
        with right:
            if extra:
                for label, value in extra.items():
                    st.metric(label, value)


def result_badge(result: str) -> None:
    """Render a coloured badge for a match result."""
    if result == "Win":
        st.success("🏆 Win")
    elif result == "Loss":
        st.error("❌ Loss")
    elif result == "Draw":
        st.warning("🤝 Draw")
    else:
        st.caption("—")


def no_data_info(msg: str = "No data available yet.") -> None:
    st.info(msg)
    st.stop()


def require_gsheets_secrets() -> bool:
    """
    Return True if GSheets secrets are configured.
    Show a warning and return False otherwise.
    """
    try:
        _ = st.secrets["gsheets"]["url"]
        _ = st.secrets["gsheets"]["creds"]
        return True
    except (KeyError, FileNotFoundError):
        st.warning(
            "**Player and captain login requires `.streamlit/secrets.toml`.**\n\n"
            "Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` "
            "and fill in your Google Sheets credentials."
        )
        return False
