# ─────────────────────────────────────────────
# pages/captain/enter_results.py
# ─────────────────────────────────────────────

import streamlit as st
from modules.auth import require_role
from modules.gsheets import update_cells
from modules.ui import page_header, no_data_info

require_role("captain", "admin")
page_header("📝 Enter Results", "Record the score and outcome for played matches.")

df_m = st.session_state.dfs["matches"]
editable = df_m[df_m["status"].isin(["Upcoming", "Played"])].sort_values("date", ascending=False)

if editable.empty:
    no_data_info("No matches to update yet. Create one first.")

# ── Match selector ────────────────────────────────────────────────────────────
options = {
    f"{row['date'].strftime('%d %b %Y')}  —  vs {row['opponent_club']}  [{row['status']}]": row["match_id"]
    for _, row in editable.iterrows()
}
chosen_label = st.selectbox("Select a match", list(options.keys()))
mid          = options[chosen_label]
match_row    = editable[editable["match_id"] == mid].iloc[0]

with st.container(border=True):
    st.write(
        f"**{match_row['competition_type']}**  ·  "
        f"{match_row['team']}  vs  {match_row['opponent_club']}"
    )
    st.caption(f"📍 {match_row.get('location', '—')}")

st.divider()

with st.form("result_form"):
    c1, c2, c3 = st.columns(3)
    with c1:
        new_status = st.selectbox(
            "Status",
            ["Upcoming", "Played", "Cancelled"],
            index=["Upcoming", "Played", "Cancelled"].index(match_row.get("status", "Upcoming")),
        )
    with c2:
        score = st.text_input(
            "Score", value=str(match_row.get("score", "")),
            placeholder="e.g. 6-3, 4-6, 7-5",
        )
    with c3:
        result_options = ["", "Win", "Loss", "Draw"]
        cur_result     = match_row.get("result", "")
        result_idx     = result_options.index(cur_result) if cur_result in result_options else 0
        result = st.selectbox("Result", result_options, index=result_idx)

    save = st.form_submit_button("💾 Save", use_container_width=True)

if save:
    update_cells("matches", "match_id", mid, {
        "status": new_status,
        "score":  score,
        "result": result,
    })
    st.success("Result saved!")
    st.rerun()
