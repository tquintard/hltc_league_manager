# ─────────────────────────────────────────────
# pages/player/calendar.py
# ─────────────────────────────────────────────

import streamlit as st
import pandas as pd
from modules.auth import require_role
from modules.ui import page_header

require_role("player", "captain", "admin")
page_header("📅 Match Calendar", "Upcoming matches and your availability status.")

pseudo = st.session_state.pseudo
df_m   = st.session_state.dfs["matches"]
df_a   = st.session_state.dfs["availability"]
df_s   = st.session_state.dfs["selections"]

upcoming = df_m[df_m["status"] == "Upcoming"].sort_values("date")

if upcoming.empty:
    st.info("No upcoming matches scheduled yet.")
    st.stop()

for _, row in upcoming.iterrows():
    mid = row["match_id"]

    # My availability
    my_avail = df_a[(df_a["match_id"] == mid) & (df_a["pseudo"] == pseudo)]
    my_status = my_avail.iloc[0]["available"] if not my_avail.empty else "⏳ Not answered"

    # Am I selected?
    is_selected = not df_s[(df_s["match_id"] == mid) & (df_s["pseudo"] == pseudo)].empty

    with st.container(border=True):
        c1, c2, c3 = st.columns([4, 2, 2])
        with c1:
            date_str = row["date"].strftime("%d %b %Y") if pd.notna(row.get("date")) else "—"
            st.write(f"**{date_str}** — vs **{row['opponent_club']}**")
            st.caption(
                f"{row['competition_type']}  ·  {row['team']}  ·  📍 {row.get('location', '—')}"
            )
        with c2:
            st.write("My response")
            st.write(my_status)
        with c3:
            if is_selected:
                st.success("✅ Selected!")
            else:
                sel_count = len(df_s[df_s["match_id"] == mid])
                if sel_count > 0:
                    st.warning("Not selected")
                else:
                    st.caption("Selection pending")
