# Fitness Gurukul Website

Multi-page Fitness Gurukul website with a responsive frontend, **Python** backend, and SQLite database.

## Stack

- Frontend: HTML pages at the repo root (`index.html`, `services.html`, …) plus `styles.css` and `app.js`
- Backend: dependency-free Python HTTP API in `server.py` (port **8000**)
- Database: SQLite file created automatically as `fitness_gurukul.sqlite3` (gitignored)
- Staff backend: `/backend` (also `/office`, `/admin`, `/staff`) — password protected

The old Node/Express server is deprecated. Use Python only.

## Run locally

### Windows (PowerShell)

`python3` often fails on Windows (Microsoft Store stub). Use one of these instead:

```powershell
copy .env.example .env
py server.py
```

or:

```powershell
python server.py
```

or double-click / run:

```powershell
.\start.bat
```

If Windows says **Python was not found** / opens the Store:

1. Install Python from https://www.python.org/downloads/
2. During setup, check **Add python.exe to PATH**
3. Open a **new** PowerShell window
4. Optional: Settings → Apps → Advanced app settings → App execution aliases → turn **OFF** `python.exe` and `python3.exe`

### macOS / Linux

```bash
cp .env.example .env
python3 server.py
```

### Any OS via npm

```bash
npm start
```

Open the website:

```text
http://127.0.0.1:8000
```

### Easy database frontend (recommended)

```text
http://127.0.0.1:8000/dashboard
```

This is a normal website page (header/nav included) connected to the live SQLite database.

1. Start the server (`py server.py` on Windows, or `python3 server.py` on macOS/Linux)
2. Open **Dashboard** in the site menu, or go to `/dashboard`
3. On your own computer it usually unlocks automatically

Local defaults:
- If you copy `.env.example`, password is `fitnessgurukul`
- If no password is set and the server is on localhost, it also defaults to `fitnessgurukul` and auto-unlocks `/dashboard`

Full staff tools also available at `/backend` (aliases: `/office`, `/admin`, `/staff`).

By default the server binds to `127.0.0.1`. To share on the same Wi-Fi:

```bash
HOST=0.0.0.0 python3 server.py
```

Then open `http://YOUR-LAPTOP-IP:8000/backend` on another device. Backend APIs still require the staff password.

## Environment

Copy `.env.example` to `.env`:

```text
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.6
ADMIN_TOKEN=fitnessgurukul
HOST=127.0.0.1
PORT=8000
```

- Without `OPENAI_API_KEY`, the chat widget answers from local website facts.
- Change `ADMIN_TOKEN` (or `ADMIN_PASSWORD`) before sharing the server beyond your machine.

## Pages

- `index.html` — home
- `about.html` — brand story
- `services.html` — plans and services
- `coaches.html` — coach directory
- `events.html` — corporate and community events
- `testimonials.html` — client stories
- `tools.html` — fitness calculators
- `contact.html` / `book-consultation.html` — lead forms
- `dashboard.html` via `/dashboard` — easy DB-connected frontend for leads
- `office.html` via `/backend` — full staff backend tools
- `owner-data.html` — optional protected SQLite viewer

## API endpoints

Public:

- `GET /api/health`
- `GET /api/content` — plans, enriched coaches (images/highlights), testimonials, live snapshot
- `GET /api/live` — rotating studio pulse + DB-backed inquiry/tool counters
- `GET /api/goals` — goal matcher catalog
- `POST /api/match` — interactive goal → plan/coach recommendation
- `GET /api/chat/status`
- `POST /api/chat`
- `POST /api/submit` — consultation and corporate event forms
- `POST /api/leads` — alias that stores into the same submissions/leads tables
- `POST /api/calculations`

The public pages are API-driven: coach grids, home minds carousel, live stats, and the goal matcher hydrate from these endpoints (with local fallbacks if the API is offline).

Protected (header `X-Admin-Token: <ADMIN_TOKEN>`):

- `GET /api/admin-data`
- `GET /api/submissions`
- `GET /api/office-stats`
- `PATCH /api/submissions/:id/status` — `new` | `contacted` | `qualified` | `closed`
- `DELETE /api/submissions/:id`

Backend UI (`/backend` → `office.html`) reads the live SQLite database and lets staff search leads, update status, export CSV, and delete records.

Sensitive paths (`.env`, `*.sqlite3`, `data/`, `server.py`, etc.) are not served as static files.

## Security notes

- Do not commit `.env`, `*.sqlite3`, or `data/*.json`
- Never share `/backend` or `owner-data.html` without the staff password
- Prefer localhost bind unless you intentionally need LAN access
- Change the default local password before exposing the server on Wi‑Fi
