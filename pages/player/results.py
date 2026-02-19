# ─────────────────────────────────────────────
# pages/player/results.py
# ─────────────────────────────────────────────

import streamlit as st
import pandas as pd
from modules.auth import require_role
from modules.ui import page_header, result_badge

require_role("player", "captain", "admin")
page_header("🏆 Results", "Latest match results.")

df_m   = st.session_state.dfs["matches"]
played = df_m[df_m["status"] == "Played"].sort_values("date", ascending=False)

if played.empty:
    st.info("No results yet.")
    st.stop()

for _, row in played.iterrows():
    date_str = row["date"].strftime("%d %b %Y") if pd.notna(row.get("date")) else "—"
    with st.container(border=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            st.write(f"**{date_str}** — vs **{row['opponent_club']}**")
            st.caption(
                f"{row['competition_type']}  ·  {row['team']}  "
                f"·  Score: **{row.get('score', '—')}**"
            )
        with c2:
            result_badge(str(row.get("result", "")))
