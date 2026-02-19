# ─────────────────────────────────────────────
# pages/captain/dashboard.py
# ─────────────────────────────────────────────

import streamlit as st
import pandas as pd
from modules.auth import require_role
from modules.ui import page_header, match_card

require_role("captain", "admin")
page_header("📊 Dashboard", "Overview of upcoming matches and availability responses.")

df_m = st.session_state.dfs["matches"]
df_a = st.session_state.dfs["availability"]
df_s = st.session_state.dfs["selections"]
df_p = st.session_state.dfs["users"]

# ── Global KPIs ───────────────────────────────────────────────────────────────
total_matches = len(df_m)
upcoming      = df_m[df_m["status"] == "Upcoming"]
played        = df_m[df_m["status"] == "Played"]
wins          = (played["result"] == "Win").sum() if not played.empty else 0
players_count = len(df_p) if not df_p.empty else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total matches",    total_matches)
k2.metric("Upcoming",         len(upcoming))
k3.metric("Wins (played)",    wins)
k4.metric("Registered players", players_count)

st.divider()

# ── Upcoming matches summary ──────────────────────────────────────────────────
st.subheader("📅 Upcoming matches")

if upcoming.empty:
    st.info("No upcoming matches. Create one in **Create Match**.")
else:
    for _, row in upcoming.sort_values("date").iterrows():
        mid   = row["match_id"]
        avail = df_a[df_a["match_id"] == mid]
        yes   = (avail["available"] == "✅ Available").sum()
        no    = (avail["available"] == "❌ Unavailable").sum()
        maybe = (avail["available"] == "❓ Maybe").sum()
        total_resp = yes + no + maybe
        sel_count  = len(df_s[df_s["match_id"] == mid])

        match_card(row, extra={
            "Responses": f"{total_resp}/{players_count}",
            "Available": yes,
            "Selected":  sel_count,
        })

st.divider()

# ── Recent results ────────────────────────────────────────────────────────────
st.subheader("🏆 Recent results")

if played.empty:
    st.info("No results yet.")
else:
    recent = played.sort_values("date", ascending=False).head(5)
    for _, row in recent.iterrows():
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                date_str = row["date"].strftime("%d %b %Y") if pd.notna(row.get("date")) else "—"
                st.write(f"**{date_str}** — vs **{row['opponent_club']}**  ·  _{row.get('score', '—')}_")
                st.caption(f"{row['competition_type']} · {row['team']}")
            with c2:
                if row.get("result") == "Win":
                    st.success("Win 🏆")
                elif row.get("result") == "Loss":
                    st.error("Loss")
                else:
                    st.caption("—")
