# Fitness Gurukul Website

Multi-page Fitness Gurukul website with a responsive frontend, **Python** backend, and SQLite database.

## Stack

- Frontend: HTML pages at the repo root (`index.html`, `services.html`, …) plus `styles.css` and `app.js`
- Backend: dependency-free Python HTTP API in `server.py` (port **8000**)
- Database: SQLite file created automatically as `fitness_gurukul.sqlite3` (gitignored)
- Two interfaces: user website (`/`) and owner portal (`/backend.html` / `backend.html`) — plus full backend at `/backend`

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

### Two interfaces

**1) User website** (customers):

```text
http://127.0.0.1:8000/
```

Public pages only: home, services, coaches, booking forms. No owner tools in the main menu.

**2) Owner portal** (you):

```text
http://127.0.0.1:8000/backend.html
```

Your private DB dashboard for leads. On your computer it usually unlocks automatically.

Aliases for the owner portal: `/owner`, `/dashboard`  
Full advanced tools: `/backend` (aliases: `/office`, `/admin`, `/staff`)

Local defaults:
- If you copy `.env.example`, password is `fitnessgurukul`
- If no password is set and the server is on localhost, it also defaults to `fitnessgurukul` and auto-unlocks `/backend.html` / `backend.html`

The public footer keeps a small **Owner login** link; it is not in the customer navigation.

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

## One-click cloud API (Render)

Deploy the Python API from this repo (free tier, no credit card):

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/saikrishnacoder/i-want-you-to-creating-a)

After deploy:
1. Copy the service URL (`https://….onrender.com`)
2. Set it in `config.js`: `window.FG_API_BASE = "https://….onrender.com";`
3. Push/redeploy Hostinger
4. Run `./scripts/verify-api.sh https://….onrender.com`
5. Open `/backend.html` with password `fitnessgurukul` (or your `ADMIN_TOKEN`)

## Deploy: Hostinger forms (works without Render)

Hostinger shared hosting can save leads with the PHP endpoints in `/api/`:

- Forms POST → `/api/submit.php` → `api/data/submissions.json`
- Challenge joins → `/api/challenge-join.php`
- Owner page → `/api/admin-data.php` (password from `api/config.php`, default `fitnessgurukul`)

Keep `config.js` as `window.FG_API_BASE = ""` for this mode. Change the password in `api/config.php` after first login.

If PHP is unavailable, forms fall back to a prefilled WhatsApp message so leads are never silently lost.

## Deploy: Hostinger site + always-on API (Render / Railway / Fly)

Optional upgrade if you want SQLite + AI chat on a cloud API:

1. **Website files** on Hostinger (HTML/CSS/JS + `/api/*.php`)
2. **Python API** (`server.py`) on Render, Railway, or Fly.io (always online)

### A) Deploy the API (pick one)

**Render (easiest)**
1. Go to [https://render.com](https://render.com) → New → Blueprint / Web Service
2. Connect this GitHub repo (`main`)
3. Runtime: Python · Start command: `python server.py`
4. Set env vars:
   - `HOST=0.0.0.0`
   - `ADMIN_TOKEN=` (choose a strong password)
   - `CORS_ORIGINS=*` (or your Hostinger domain)
5. Deploy → copy the URL, e.g. `https://fitness-gurukul-api.onrender.com`

**Railway**
1. [https://railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Start command: `python server.py`
3. Add the same env vars as above
4. Generate a public domain and copy it

**Fly.io**
```bash
fly launch
fly secrets set ADMIN_TOKEN=your-strong-password CORS_ORIGINS=*
fly deploy
```

Health check: open `https://YOUR-API-URL/api/health` — should return `{"ok": true, ...}`.

### B) Point the Hostinger website at the API

Edit `config.js` on Hostinger (or in Git then redeploy):

```js
window.FG_API_BASE = "https://YOUR-API-URL";
```

Example:

```js
window.FG_API_BASE = "https://fitness-gurukul-api.onrender.com";
```

Leave it as `""` only when the site and API are on the same origin (local `server.py`).

**This one setting is what keeps leads in your backend:**
- Website forms → `POST {FG_API_BASE}/api/submit` → SQLite on the cloud API
- Challenge joins → `POST {FG_API_BASE}/api/challenge-join` → same SQLite
- Owner page `backend.html` → `GET {FG_API_BASE}/api/admin-data` → same SQLite

So Hostinger only hosts the pages; the cloud API owns the database.

### C) Redeploy Hostinger

Pull/upload the latest `main` (includes `config.js`) and make sure your edited API URL is live.

Then forms, quiz, live stats, chat, and `backend.html` keep working with your laptop off. Open `https://yoursite.com/backend.html` and unlock with the same `ADMIN_TOKEN` from Render/Railway/Fly — new leads appear there.

**Notes**
- Free Render apps may sleep after idle; first request can take ~30s to wake.
- SQLite on free tiers is usually ephemeral (resets on redeploy). For permanent leads, use a paid disk/volume or export regularly from the owner backend.

## Pages

- `index.html` — home
- `about.html` — brand story
- `services.html` — plans and services
- `coaches.html` — coach directory
- `events.html` — corporate and community events
- `testimonials.html` — client stories
- `tools.html` — fitness calculators
- `contact.html` / `book-consultation.html` — lead forms
- `dashboard.html` via `/backend.html` / `backend.html` — owner portal (your DB interface)
- `office.html` via `/backend` — full advanced backend tools
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
