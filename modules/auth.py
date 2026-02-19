# ─────────────────────────────────────────────
# modules/auth.py — Authentication & authorisation
# ─────────────────────────────────────────────

from __future__ import annotations

import hashlib
import streamlit as st

from config.settings import ALL_ROLES


# ── Session state defaults ────────────────────────────────────────────────────

SESSION_DEFAULTS: dict = {
    "authenticated": False,
    "pseudo":        None,   # logged-in username
    "roles":         [],     # list of active roles  e.g. ["admin","captain"]
    "display_name":  None,
    "sh":            None,   # gspread Spreadsheet object
    "worksheets":    {},     # dict[str, gspread.Worksheet]
    "dfs":           {},     # dict[str, pd.DataFrame]
}


def init_session_state() -> None:
    """Ensure all session keys are initialised (idempotent)."""
    for key, default in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def logout() -> None:
    """Clear authentication state and rerun."""
    for key, default in SESSION_DEFAULTS.items():
        st.session_state[key] = default
    st.rerun()


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.strip().encode()).hexdigest()


def verify_password(password: str, stored_hash: str) -> bool:
    return hash_password(password) == stored_hash


# ── Login helpers ─────────────────────────────────────────────────────────────

def login_user(pseudo: str, roles: list[str], display_name: str, sh, worksheets: dict, dfs: dict) -> None:
    """Set session state for an authenticated user."""
    st.session_state.update({
        "authenticated": True,
        "pseudo":        pseudo,
        "roles":         roles,
        "display_name":  display_name or pseudo,
        "sh":            sh,
        "worksheets":    worksheets,
        "dfs":           dfs,
    })


def try_login_with_password(pseudo: str, password: str) -> tuple[bool, str]:
    """
    Attempt to log in using pseudo + password against the users sheet.
    Returns (success, error_message).
    Assumes GSheets is already connected (via secrets.toml).
    """
    from modules.gsheets import build_connection_from_secrets, open_all_worksheets, load_all

    try:
        _, sh = build_connection_from_secrets()
    except Exception as e:
        return False, f"Could not connect to Google Sheets: {e}"

    worksheets = open_all_worksheets(sh)
    dfs        = load_all(sh)
    users_df   = dfs.get("users")

    if users_df is None or users_df.empty:
        return False, "No users registered yet. Ask your admin to create your account."

    match = users_df[users_df["pseudo"] == pseudo]
    if match.empty:
        return False, "Unknown username."

    row = match.iloc[0]
    if not verify_password(password, str(row["password_hash"])):
        return False, "Incorrect password."

    roles        = [r.strip() for r in str(row.get("roles", "player")).split(",") if r.strip()]
    display_name = str(row.get("display_name", pseudo))
    login_user(pseudo, roles, display_name, sh, worksheets, dfs)
    return True, ""


def try_login_as_admin(creds_raw: str, sheet_url: str) -> tuple[bool, str]:
    """
    Log in as site admin using raw GSheets JSON credentials.
    Creates/upserts an admin account in the users sheet if needed.
    Returns (success, error_message).
    NOTE: deliberately avoids session_state during the login flow.
    """
    import json
    import pandas as pd
    from modules.gsheets import build_connection, open_all_worksheets, load_all
    from config.settings import SHEET_SCHEMAS

    try:
        _, sh = build_connection(creds_raw, sheet_url)
    except json.JSONDecodeError:
        return False, "Invalid JSON credentials."
    except Exception as e:
        return False, f"Connection error: {e}"

    worksheets = open_all_worksheets(sh)
    dfs        = load_all(sh)

    # Seed admin account on first connection ──────────────────────────────
    users_df     = dfs["users"]
    admin_pseudo = "admin"

    if users_df.empty or admin_pseudo not in users_df["pseudo"].values:
        # Write directly to the worksheet — session_state not yet available
        users_ws = worksheets["users"]
        users_ws.append_row([
            admin_pseudo,
            hash_password("changeme"),
            "admin,captain,player",
            "Admin",
        ])
        # Reload locally without touching session_state
        records  = users_ws.get_all_records()
        dfs["users"] = pd.DataFrame(records) if records else pd.DataFrame(columns=SHEET_SCHEMAS["users"])

    row          = dfs["users"][dfs["users"]["pseudo"] == admin_pseudo].iloc[0]
    roles        = [r.strip() for r in str(row.get("roles", "admin")).split(",") if r.strip()]
    display_name = str(row.get("display_name", "Admin"))
    login_user(admin_pseudo, roles, display_name, sh, worksheets, dfs)
    return True, ""


# ── Role guards ───────────────────────────────────────────────────────────────

def has_role(*roles: str) -> bool:
    """Return True if the current user has at least one of the given roles."""
    user_roles = st.session_state.get("roles", [])
    return any(r in user_roles for r in roles)


def require_role(*roles: str) -> None:
    """
    Stop page rendering and show an error if the user lacks the required role.
    Call at the top of any page that needs role protection.
    """
    if not st.session_state.get("authenticated"):
        st.error("🔒 You must be logged in to access this page.")
        st.stop()
    if not has_role(*roles):
        st.error(f"🚫 This page requires one of these roles: {', '.join(roles)}.")
        st.stop()
