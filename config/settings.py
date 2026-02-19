# ─────────────────────────────────────────────
# config/settings.py — App-wide constants
# ─────────────────────────────────────────────

APP_TITLE = "Tennis Club"
APP_ICON  = "🎾"

# Google OAuth scopes
GSHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Spreadsheet tab names and their column schemas
SHEET_SCHEMAS: dict[str, list[str]] = {
    "users": [
        "pseudo",        # unique login name
        "password_hash", # sha-256 hex digest
        "roles",         # comma-separated: admin, captain, player
        "display_name",  # optional friendly name
    ],
    "matches": [
        "match_id",
        "date",
        "competition_type",
        "team",
        "opponent_club",
        "location",
        "status",   # Upcoming | Played | Cancelled
        "score",
        "result",   # Win | Loss | Draw | ""
    ],
    "availability": [
        "match_id",
        "pseudo",
        "available",  # ✅ Available | ❌ Unavailable | ❓ Maybe
        "comment",
    ],
    "selections": [
        "match_id",
        "pseudo",
    ],
}

# All possible roles (order matters for display)
ALL_ROLES    = ["admin", "captain", "player"]
AVAIL_OPTIONS = ["✅ Available", "❌ Unavailable", "❓ Maybe"]

COMPETITION_TYPES = ["Interclubs", "Team Championship"]
MATCH_STATUSES    = ["Upcoming", "Played", "Cancelled"]
