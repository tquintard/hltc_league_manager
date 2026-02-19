# ─────────────────────────────────────────────
# pages/admin/manage_accounts.py
# ─────────────────────────────────────────────

import streamlit as st
import pandas as pd
from modules.auth import require_role, hash_password
from modules.gsheets import append_row, update_cells, delete_rows_where, reload_sheet
from modules.ui import page_header
from config.settings import ALL_ROLES


require_role("admin")
page_header("👤 Manage Accounts", "Create and manage user accounts and their roles.")

df_users = st.session_state.dfs["users"]

# ── Current accounts ──────────────────────────────────────────────────────────
st.subheader("Current accounts")

if df_users.empty:
    st.info("No accounts found.")
else:
    for i, row in df_users.iterrows():
        pseudo       = str(row["pseudo"])
        current_roles = [r.strip() for r in str(row.get("roles", "")).split(",") if r.strip()]
        display      = str(row.get("display_name", pseudo))

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 2, 3, 1])

            with c1:
                new_display = st.text_input(
                    "Display name", value=display, key=f"dn_{pseudo}",
                    label_visibility="collapsed",
                )

            with c2:
                new_roles = st.multiselect(
                    "Roles", ALL_ROLES, default=current_roles,
                    key=f"roles_{pseudo}", label_visibility="collapsed",
                )

            with c3:
                new_pw = st.text_input(
                    "New password (leave blank to keep)", type="password",
                    key=f"pw_{pseudo}", placeholder="New password…",
                    label_visibility="collapsed",
                )

            with c4:
                save_btn = st.button("💾", key=f"save_{pseudo}", help="Save changes")
                del_btn  = st.button("🗑️", key=f"del_{pseudo}",  help="Delete account")

            if save_btn:
                updates: dict = {
                    "roles":        ",".join(new_roles),
                    "display_name": new_display,
                }
                if new_pw.strip():
                    updates["password_hash"] = hash_password(new_pw.strip())
                update_cells("users", "pseudo", pseudo, updates)
                st.success(f"Account **{pseudo}** updated.")
                st.rerun()

            if del_btn:
                if pseudo == st.session_state.pseudo:
                    st.error("You cannot delete your own account.")
                else:
                    delete_rows_where("users", "pseudo", pseudo)
                    st.success(f"Account **{pseudo}** deleted.")
                    st.rerun()

st.divider()

# ── Create new account ────────────────────────────────────────────────────────
st.subheader("Create a new account")

with st.form("create_account_form", clear_on_submit=True):
    ca1, ca2 = st.columns(2)
    with ca1:
        new_pseudo  = st.text_input("Username (pseudo) *", placeholder="e.g. john_doe")
        new_display = st.text_input("Display name",        placeholder="e.g. John Doe")
    with ca2:
        new_pw      = st.text_input("Password *", type="password")
        new_roles   = st.multiselect("Roles *", ALL_ROLES, default=["player"])

    submitted = st.form_submit_button("➕ Create account", use_container_width=True)

if submitted:
    if not new_pseudo.strip() or not new_pw.strip() or not new_roles:
        st.error("Username, password and at least one role are required.")
    elif new_pseudo.strip() in (st.session_state.dfs["users"]["pseudo"].values if not st.session_state.dfs["users"].empty else []):
        st.warning(f"Username **{new_pseudo}** already exists.")
    else:
        append_row("users", {
            "pseudo":        new_pseudo.strip(),
            "password_hash": hash_password(new_pw.strip()),
            "roles":         ",".join(new_roles),
            "display_name":  new_display.strip() or new_pseudo.strip(),
        })
        st.success(f"Account **{new_pseudo}** created with roles: {', '.join(new_roles)}.")
        st.rerun()
