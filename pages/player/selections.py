# ─────────────────────────────────────────────
# pages/player/selections.py
# ─────────────────────────────────────────────

import streamlit as st
import pandas as pd
from modules.auth import require_role
from modules.ui import page_header

require_role("player", "captain", "admin")
page_header("👥 Selections", "See who has been selected for each upcoming match.")

pseudo = st.session_state.pseudo
df_m   = st.session_state.dfs["matches"]
df_s   = st.session_state.dfs["selections"]

upcoming = df_m[df_m["status"] == "Upcoming"].sort_values("date")

if upcoming.empty:
    st.info("No upcoming matches.")
    st.stop()

for _, row in upcoming.iterrows():
    mid      = row["match_id"]
    date_str = row["date"].strftime("%d %b %Y") if pd.notna(row.get("date")) else "—"
    sel      = df_s[df_s["match_id"] == mid]["pseudo"].tolist()
    is_me    = pseudo in sel

    with st.container(border=True):
        st.write(f"**{date_str}** — vs **{row['opponent_club']}**")
        st.caption(f"{row['competition_type']}  ·  {row['team']}")

        if not sel:
            st.caption("⏳ Selection not published yet.")
        else:
            players_str = "  ·  ".join(f"**{p}**" if p == pseudo else p for p in sel)
            if is_me:
                st.success(f"🎾 You are selected!  —  {players_str}")
            else:
                st.info(f"Selected players: {players_str}")
