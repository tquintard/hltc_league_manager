# ─────────────────────────────────────────────
# pages/captain/create_match.py
# ─────────────────────────────────────────────

import re
import streamlit as st
from datetime import date
from modules.auth import require_role
from modules.gsheets import append_row
from modules.ui import page_header
from config.settings import COMPETITION_TYPES

require_role("captain", "admin")
page_header("➕ Create a Match", "Schedule a new match. It will appear automatically in player availability polls.")

with st.form("create_match_form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1:
        match_date  = st.date_input("📅 Date *", value=date.today())
        competition = st.selectbox("🏆 Competition type *", COMPETITION_TYPES)
        team        = st.text_input("👥 Our team *", placeholder="e.g. Men's Team 1")
    with c2:
        opponent    = st.text_input("🏟️ Opponent club *", placeholder="e.g. TC Paris")
        location    = st.text_input("📍 Location", placeholder="e.g. Home / Away / Court 3")

    submitted = st.form_submit_button("💾 Create match", use_container_width=True)

if submitted:
    if not opponent.strip() or not team.strip():
        st.error("Opponent club and team are required.")
    else:
        slug = re.sub(r"[^a-z0-9]", "", opponent.lower())[:10]
        mid  = f"{match_date.strftime('%Y%m%d')}_{slug}"

        existing = st.session_state.dfs["matches"]
        if not existing.empty and mid in existing["match_id"].values:
            st.error("A match with this date and opponent already exists.")
        else:
            append_row("matches", {
                "match_id":         mid,
                "date":             match_date.strftime("%Y-%m-%d"),
                "competition_type": competition,
                "team":             team.strip(),
                "opponent_club":    opponent.strip(),
                "location":         location.strip(),
                "status":           "Upcoming",
                "score":            "",
                "result":           "",
            })
            st.success(f"✅ Match created: **{match_date.strftime('%d %b %Y')}** vs **{opponent.strip()}**")
            st.balloons()

# ── Existing upcoming matches (read-only preview) ─────────────────────────────
st.divider()
st.subheader("Scheduled upcoming matches")

df_m = st.session_state.dfs["matches"]
upcoming = df_m[df_m["status"] == "Upcoming"].sort_values("date")

if upcoming.empty:
    st.info("No upcoming matches yet.")
else:
    display = upcoming[["date", "competition_type", "team", "opponent_club", "location"]].copy()
    display["date"] = display["date"].dt.strftime("%d %b %Y")
    display.columns = ["Date", "Competition", "Team", "Opponent", "Location"]
    st.dataframe(display, use_container_width=True, hide_index=True)
