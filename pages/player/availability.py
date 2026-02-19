# ─────────────────────────────────────────────
# pages/player/availability.py
# ─────────────────────────────────────────────

import streamlit as st
import pandas as pd
from modules.auth import require_role
from modules.gsheets import upsert_availability
from modules.ui import page_header
from config.settings import AVAIL_OPTIONS

require_role("player", "captain", "admin")
page_header("🗳️ My Availability", "Let your captain know if you can make each upcoming match.")

pseudo = st.session_state.pseudo
df_m   = st.session_state.dfs["matches"]
df_a   = st.session_state.dfs["availability"]

upcoming = df_m[df_m["status"] == "Upcoming"].sort_values("date")

if upcoming.empty:
    st.info("No upcoming matches to respond to yet.")
    st.stop()

for _, row in upcoming.iterrows():
    mid = row["match_id"]
    date_str = row["date"].strftime("%d %b %Y") if pd.notna(row.get("date")) else "—"

    my_avail        = df_a[(df_a["match_id"] == mid) & (df_a["pseudo"] == pseudo)]
    current_avail   = my_avail.iloc[0]["available"] if not my_avail.empty else AVAIL_OPTIONS[0]
    current_comment = str(my_avail.iloc[0].get("comment", "")) if not my_avail.empty else ""
    avail_idx = AVAIL_OPTIONS.index(current_avail) if current_avail in AVAIL_OPTIONS else 0

    with st.container(border=True):
        st.write(f"**{date_str}** — vs **{row['opponent_club']}**")
        st.caption(f"{row['competition_type']}  ·  {row['team']}  ·  📍 {row.get('location', '—')}")

        col_av, col_cm, col_btn = st.columns([2, 3, 1])
        with col_av:
            avail_choice = st.selectbox(
                "Availability",
                AVAIL_OPTIONS,
                index=avail_idx,
                key=f"avail_{mid}",
                label_visibility="collapsed",
            )
        with col_cm:
            comment = st.text_input(
                "Comment",
                value=current_comment,
                placeholder="Optional comment…",
                key=f"comment_{mid}",
                label_visibility="collapsed",
            )
        with col_btn:
            if st.button("Save", key=f"save_{mid}", use_container_width=True):
                upsert_availability(mid, pseudo, avail_choice, comment)
                st.success("Saved!")
                st.rerun()
