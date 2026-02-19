# 🎾 Tennis Club — Match Manager

A multi-role Streamlit application for managing tennis club matches, availability polls, player selections and statistics. Data is stored in Google Sheets.

---

## 📁 Project structure

```
tennis_club/
├── app.py                          ← Entry point & dynamic navigation
├── requirements.txt
├── README.md
│
├── .streamlit/
│   ├── config.toml                 ← Streamlit theme & server settings
│   └── secrets.toml.example        ← Template — copy & fill in
│
├── config/
│   ├── __init__.py
│   └── settings.py                 ← App-wide constants (schemas, roles, options)
│
├── modules/
│   ├── __init__.py
│   ├── auth.py                     ← Session init, login, logout, role guards
│   ├── gsheets.py                  ← Google Sheets client & CRUD helpers
│   └── ui.py                       ← Shared reusable UI components
│
└── pages/
    ├── login.py                    ← Login screen (admin tab + user tab)
    │
    ├── admin/
    │   ├── manage_accounts.py      ← Create / edit / delete user accounts
    │   └── site_settings.py        ← App info, secrets check, force reload
    │
    ├── captain/
    │   ├── dashboard.py            ← Overview: upcoming matches + recent results
    │   ├── create_match.py         ← Schedule a new match
    │   ├── enter_results.py        ← Enter score and outcome
    │   ├── availability_manager.py ← View responses, select players
    │   └── statistics.py           ← Charts and performance analysis
    │
    └── player/
        ├── calendar.py             ← Upcoming matches + my response status
        ├── availability.py         ← Respond to availability polls
        ├── results.py              ← View match results
        └── selections.py           ← See team selections per match
```

---

## 🚀 Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 👥 Roles

| Role        | Who                     | Access                                                                 |
|-------------|-------------------------|------------------------------------------------------------------------|
| **admin**   | Site owner (you)        | All sections. Manages user accounts and settings.                     |
| **captain** | Team captain            | Captain section (create matches, manage availability, enter results) + Player section. |
| **player**  | Club member             | Player section (calendar, availability poll, results, selections).    |

Roles are **combinable**: the admin can also be captain and/or player. A captain can also be a player. Assign multiple roles per account in **Admin → Manage Accounts**.

---

## ⚙️ Google Sheets setup

### 1. Create a Google Cloud project
- Go to https://console.cloud.google.com/ → create a project
- Enable **Google Sheets API** and **Google Drive API**

### 2. Create a service account
- *IAM & Admin → Service Accounts* → Create
- Generate a **JSON key** and download it

### 3. Create a Google Sheets file
- Share it with the service account email (Editor role)
- The app auto-creates these tabs on first connection:

| Tab            | Columns                                                          |
|----------------|------------------------------------------------------------------|
| `users`        | pseudo, password_hash, roles, display_name                      |
| `matches`      | match_id, date, competition_type, team, opponent_club, location, status, score, result |
| `availability` | match_id, pseudo, available, comment                            |
| `selections`   | match_id, pseudo                                                 |

---

## 🔐 Authentication

### Site Admin
Login via **Admin tab** on the login screen by pasting:
- The full content of the service account JSON key
- The Google Sheets URL

On first connection, an `admin` account is automatically created in the `users` sheet with:
- Username: `admin`
- Password: `changeme` ← **change this immediately** in *Admin → Manage Accounts*

### Captains & Players
Login via **Captain / Player tab** with a username (pseudo) and password.
Accounts must be created by the admin in *Admin → Manage Accounts*.

---

## 🔑 secrets.toml (required for captain/player login)

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# then edit .streamlit/secrets.toml with your values
```

```toml
[gsheets]
url    = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
creds  = '{ ...service account JSON as single-line string... }'
```

> **Streamlit Cloud**: add these secrets in the app's Settings → Secrets panel instead of a local file.

> **Never commit `secrets.toml` to version control.** It is already in `.gitignore` by convention.

---

## 🔄 Typical workflow

1. **Admin** connects via JSON → changes default password → creates captain and player accounts
2. **Captain** creates matches → players receive availability polls
3. **Players** log in → respond to availability for each match
4. **Captain** reviews responses in *Availability Manager* → selects players
5. Players see their selection in *Selections*
6. After the match, **Captain** enters score and result in *Enter Results*
7. **Captain** reviews stats in *Statistics*

---

## 🛠️ Extending the app

- **Add a new role**: update `ALL_ROLES` in `config/settings.py` and add the role guard in `app.py`
- **Add a new sheet**: add schema to `SHEET_SCHEMAS` in `config/settings.py`
- **Add a page**: create the file in the appropriate `pages/` subfolder and register it in `app.py`
