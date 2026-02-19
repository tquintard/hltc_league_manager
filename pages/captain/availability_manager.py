# ─────────────────────────────────────────────
# pages/captain/availability_manager.py
# ─────────────────────────────────────────────

import streamlit as st
import pandas as pd
from modules.auth import require_role
from modules.gsheets import append_row, delete_rows_where
from modules.ui import page_header, no_data_info
from config.settings import AVAIL_OPTIONS

require_role("captain", "admin")
page_header("🗳️ Availability Manager", "Review player responses and finalise selection for each match.")

df_m = st.session_state.dfs["matches"]
df_a = st.session_state.dfs["availability"]
df_s = st.session_state.dfs["selections"]
df_u = st.session_state.dfs["users"]

upcoming = df_m[df_m["status"] == "Upcoming"].sort_values("date")
if upcoming.empty:
    no_data_info("No upcoming matches. Create one in **Create Match**.")

# ── Match picker ──────────────────────────────────────────────────────────────
options = {
    f"{row['date'].strftime('%d %b %Y')}  —  vs {row['opponent_club']}": row["match_id"]
    for _, row in upcoming.iterrows()
}
chosen_label = st.selectbox("Select a match", list(options.keys()))
mid          = options[chosen_label]
match_row    = upcoming[upcoming["match_id"] == mid].iloc[0]

st.subheader(f"vs {match_row['opponent_club']}  ·  {match_row['date'].strftime('%d %b %Y')}")
st.caption(f"{match_row['competition_type']}  ·  {match_row['team']}  ·  📍 {match_row.get('location','—')}")
st.divider()

# ── Players with roles containing "player" ────────────────────────────────────
all_players: list[str] = []
if not df_u.empty:
    all_players = df_u[df_u["roles"].str.contains("player", na=False)]["pseudo"].tolist()

avail_df = df_a[df_a["match_id"] == mid]

# ── Availability summary ──────────────────────────────────────────────────────
st.subheader("📋 Availability responses")

summary = []
for p in all_players:
    row = avail_df[avail_df["pseudo"] == p]
    if not row.empty:
        summary.append({
            "Player":   p,
            "Response": row.iloc[0]["available"],
            "Comment":  str(row.iloc[0].get("comment", "")),
        })
    else:
        summary.append({"Player": p, "Response": "⏳ No response", "Comment": ""})

df_summary = pd.DataFrame(summary) if summary else pd.DataFrame(columns=["Player", "Response", "Comment"])
st.dataframe(df_summary, use_container_width=True, hide_index=True)

# KPI strip
yes   = (avail_df["available"] == "✅ Available").sum()
no    = (avail_df["available"] == "❌ Unavailable").sum()
maybe = (avail_df["available"] == "❓ Maybe").sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric("✅ Available",      yes)
k2.metric("❌ Unavailable",    no)
k3.metric("❓ Maybe",          maybe)
k4.metric("⏳ No response",    len(all_players) - yes - no - maybe)

st.divider()

# ── Player selection ──────────────────────────────────────────────────────────
st.subheader("✅ Select players for this match")

available_pseudos = avail_df[avail_df["available"] == "✅ Available"]["available"].index.map(
    lambda i: avail_df.loc[i, "pseudo"]
).tolist()
maybe_pseudos = avail_df[avail_df["available"] == "❓ Maybe"]["available"].index.map(
    lambda i: avail_df.loc[i, "pseudo"]
).tolist()

# Build display helper
def fmt(p: str) -> str:
    if p in available_pseudos:
        return f"✅ {p}"
    if p in maybe_pseudos:
        return f"❓ {p}"
    no_resp = [r["Player"] for r in summary if r["Response"] == "⏳ No response"]
    if p in no_resp:
        return f"⏳ {p}"
    return f"❌ {p}"

# Sort: available first, then maybe, then others
sorted_players = (
    [p for p in all_players if p in available_pseudos] +
    [p for p in all_players if p in maybe_pseudos] +
    [p for p in all_players if p not in available_pseudos and p not in maybe_pseudos]
)

current_sel = df_s[df_s["match_id"] == mid]["pseudo"].tolist()

st.caption("Available and Maybe players are shown first.")
selected = st.multiselect(
    "Selected players",
    options=sorted_players,
    default=[p for p in current_sel if p in sorted_players],
    format_func=fmt,
)

if st.button("💾 Save selection", use_container_width=True):
    delete_rows_where("selections", "match_id", mid)
    for p in selected:
        append_row("selections", {"match_id": mid, "pseudo": p})
    if selected:
        st.success(f"Selection saved: {', '.join(selected)}")
    else:
        st.success("Selection cleared (no players selected).")
    st.rerun()
