# ─────────────────────────────────────────────
# pages/captain/statistics.py
# ─────────────────────────────────────────────

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from modules.auth import require_role
from modules.ui import page_header, no_data_info

require_role("captain", "admin")
page_header("📈 Statistics", "Team performance, trends and player involvement.")

df_m = st.session_state.dfs["matches"]
df_s = st.session_state.dfs["selections"]
played = df_m[df_m["status"] == "Played"].copy()

if played.empty:
    no_data_info("No played matches yet.")

played["win"] = (played["result"] == "Win").astype(int)
total  = len(played)
wins   = played["win"].sum()
losses = total - wins
wr     = round(wins / total * 100) if total else 0

# ── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Matches played", total)
k2.metric("Wins",   wins)
k3.metric("Losses", losses)
k4.metric("Win rate", f"{wr}%")

st.divider()

# ── Row 1: pie + bar ──────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Overall results")
    fig_pie = px.pie(
        values=[wins, losses],
        names=["Wins", "Losses"],
        color_discrete_sequence=["#2d6a4f", "#e63946"],
        hole=0.45,
    )
    fig_pie.update_traces(textinfo="percent+label")
    fig_pie.update_layout(showlegend=False, margin=dict(t=10, b=10))
    st.plotly_chart(fig_pie, use_container_width=True)

with col_b:
    st.subheader("By competition type")
    cs = (
        played.groupby(["competition_type", "result"])
        .size().reset_index(name="count")
    )
    fig_bar = px.bar(
        cs, x="competition_type", y="count", color="result", barmode="group",
        color_discrete_map={"Win": "#2d6a4f", "Loss": "#e63946", "Draw": "#f4a261"},
        labels={"competition_type": "Competition", "count": "Matches", "result": ""},
    )
    fig_bar.update_layout(margin=dict(t=10, b=10), legend_title_text="")
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Cumulative trend ──────────────────────────────────────────────────────────
st.subheader("📈 Cumulative results over time")
s = played.sort_values("date").copy()
s["cumul_wins"]   = s["win"].cumsum()
s["cumul_losses"] = (1 - s["win"]).cumsum()
s["date_str"]     = s["date"].dt.strftime("%d/%m/%Y")

fig_evo = go.Figure()
fig_evo.add_trace(go.Scatter(
    x=s["date_str"], y=s["cumul_wins"], name="Wins",
    line=dict(color="#2d6a4f", width=3),
    fill="tozeroy", fillcolor="rgba(45,106,79,0.12)",
))
fig_evo.add_trace(go.Scatter(
    x=s["date_str"], y=s["cumul_losses"], name="Losses",
    line=dict(color="#e63946", width=2, dash="dot"),
))
fig_evo.update_layout(
    xaxis_title="Date", yaxis_title="Cumulative matches",
    margin=dict(t=10, b=10), legend_title_text="",
)
st.plotly_chart(fig_evo, use_container_width=True)

# ── Record vs opponent clubs ──────────────────────────────────────────────────
st.subheader("⚔️ Record against opponent clubs")
adv = (
    played.groupby("opponent_club")
    .agg(matches=("win", "count"), wins=("win", "sum"))
    .reset_index()
)
adv["losses"] = adv["matches"] - adv["wins"]
adv = adv.sort_values("matches", ascending=False).head(10)

fig_adv = px.bar(
    adv, y="opponent_club", x=["wins", "losses"],
    barmode="stack", orientation="h",
    color_discrete_map={"wins": "#2d6a4f", "losses": "#e63946"},
    labels={"opponent_club": "Club", "value": "Matches", "variable": ""},
)
fig_adv.update_layout(margin=dict(t=10, b=10), legend_title_text="")
st.plotly_chart(fig_adv, use_container_width=True)

# ── Player participation ──────────────────────────────────────────────────────
if not df_s.empty:
    st.subheader("👥 Player participation (selections)")
    sel_played = df_s[df_s["match_id"].isin(played["match_id"])]
    if not sel_played.empty:
        counts = sel_played["pseudo"].value_counts().reset_index()
        counts.columns = ["Player", "Selections"]
        fig_sel = px.bar(
            counts.head(15), x="Player", y="Selections",
            color_discrete_sequence=["#2d6a4f"],
        )
        fig_sel.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig_sel, use_container_width=True)
