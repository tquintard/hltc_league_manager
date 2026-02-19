# ─────────────────────────────────────────────
# modules/gsheets.py — Google Sheets helpers
# ─────────────────────────────────────────────

from __future__ import annotations

import json
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

from config.settings import GSHEETS_SCOPES, SHEET_SCHEMAS


# ── Client factory ────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def _make_client(creds_json_str: str) -> gspread.Client:
    """Create and cache a gspread client from a JSON credentials string."""
    info  = json.loads(creds_json_str)
    creds = Credentials.from_service_account_info(info, scopes=GSHEETS_SCOPES)
    return gspread.authorize(creds)


def build_connection(creds_raw: str, sheet_url: str) -> tuple[gspread.Client, gspread.Spreadsheet]:
    """Return (client, spreadsheet) from raw JSON credentials and URL."""
    client = _make_client(creds_raw)
    sh     = client.open_by_url(sheet_url)
    return client, sh


def build_connection_from_secrets() -> tuple[gspread.Client, gspread.Spreadsheet]:
    """
    Return (client, spreadsheet) using credentials stored in st.secrets.

    Supports two formats in secrets.toml:

    Format A — TOML native (recommended, no JSON escaping issues):
        [gsheets]
        url = "https://docs.google.com/..."
        [gsheets_creds]
        type = "service_account"
        project_id = "..."
        private_key = \"\"\"-----BEGIN RSA PRIVATE KEY-----\\n...\\n-----END RSA PRIVATE KEY-----\\n\"\"\"
        client_email = "..."
        ... (all other fields from the JSON key file)

    Format B — JSON string (legacy):
        [gsheets]
        url   = "https://docs.google.com/..."
        creds = '{"type":"service_account",...}'
    """
    url = st.secrets["gsheets"]["url"]

    # Format A: dedicated [gsheets_creds] TOML section (preferred)
    if "gsheets_creds" in st.secrets:
        creds_info = dict(st.secrets["gsheets_creds"])
        # Streamlit may escape \n in private_key — normalize it
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        creds  = Credentials.from_service_account_info(creds_info, scopes=GSHEETS_SCOPES)
        client = gspread.authorize(creds)
        sh     = client.open_by_url(url)
        return client, sh

    # Format B: JSON string under gsheets.creds (legacy fallback)
    creds_raw = st.secrets["gsheets"]["creds"]
    if not isinstance(creds_raw, str):
        creds_raw = json.dumps(dict(creds_raw))
    return build_connection(creds_raw, url)


# ── Worksheet helpers ─────────────────────────────────────────────────────────

def open_or_create_ws(sh: gspread.Spreadsheet, name: str) -> gspread.Worksheet:
    """Return worksheet by name, creating it with header row if absent."""
    try:
        return sh.worksheet(name)
    except gspread.WorksheetNotFound:
        cols = SHEET_SCHEMAS[name]
        ws   = sh.add_worksheet(title=name, rows=1000, cols=len(cols))
        ws.append_row(cols)
        return ws


def open_all_worksheets(sh: gspread.Spreadsheet) -> dict[str, gspread.Worksheet]:
    """Open (or create) every sheet defined in SHEET_SCHEMAS."""
    return {name: open_or_create_ws(sh, name) for name in SHEET_SCHEMAS}


# ── Data loading ──────────────────────────────────────────────────────────────

def _parse_df(name: str, records: list[dict]) -> pd.DataFrame:
    cols = SHEET_SCHEMAS[name]
    df   = pd.DataFrame(records) if records else pd.DataFrame(columns=cols)
    if name == "matches" and not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def load_all(sh: gspread.Spreadsheet) -> dict[str, pd.DataFrame]:
    """Load every worksheet into a dict of DataFrames."""
    dfs = {}
    for name in SHEET_SCHEMAS:
        ws      = open_or_create_ws(sh, name)
        records = ws.get_all_records()
        dfs[name] = _parse_df(name, records)
    return dfs


def reload_sheet(name: str) -> None:
    """Reload a single sheet into st.session_state.dfs[name]."""
    ws      = st.session_state.worksheets[name]
    records = ws.get_all_records()
    st.session_state.dfs[name] = _parse_df(name, records)


# ── Write operations ──────────────────────────────────────────────────────────

def append_row(sheet: str, row: dict) -> None:
    """Append a new row and refresh the cached DataFrame."""
    ws = st.session_state.worksheets[sheet]
    ws.append_row([row.get(c, "") for c in SHEET_SCHEMAS[sheet]])
    reload_sheet(sheet)


def update_cells(sheet: str, match_col: str, match_val: str, updates: dict) -> None:
    """
    Find the first row where match_col == match_val and apply updates.
    updates = {col_name: new_value, ...}
    """
    ws   = st.session_state.worksheets[sheet]
    df   = st.session_state.dfs[sheet]
    cols = SHEET_SCHEMAS[sheet]
    idxs = df.index[df[match_col].astype(str) == str(match_val)].tolist()
    if not idxs:
        return
    row_num = idxs[0] + 2  # 1-indexed + header
    for col_name, value in updates.items():
        col_num = cols.index(col_name) + 1
        ws.update_cell(row_num, col_num, value)
    reload_sheet(sheet)


def delete_rows_where(sheet: str, match_col: str, match_val: str) -> None:
    """Delete all rows where match_col == match_val."""
    ws   = st.session_state.worksheets[sheet]
    df   = st.session_state.dfs[sheet]
    idxs = df.index[df[match_col].astype(str) == str(match_val)].tolist()
    for i in reversed(idxs):
        ws.delete_rows(i + 2)
    reload_sheet(sheet)


def upsert_availability(match_id: str, pseudo: str, available: str, comment: str) -> None:
    """Insert or update an availability row for (match_id, pseudo)."""
    ws   = st.session_state.worksheets["availability"]
    df   = st.session_state.dfs["availability"]
    mask = (df["match_id"].astype(str) == str(match_id)) & (df["pseudo"] == pseudo)
    if mask.any():
        idx     = df.index[mask][0]
        row_num = idx + 2
        ws.update(f"C{row_num}:D{row_num}", [[available, comment]])
        reload_sheet("availability")
    else:
        append_row("availability", {
            "match_id": match_id,
            "pseudo":   pseudo,
            "available": available,
            "comment":  comment,
        })
