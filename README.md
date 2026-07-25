# Fitness Gurukul Website

Multi-page Fitness Gurukul website with a responsive frontend, **Python** backend, and SQLite database.

## Stack

- Frontend: HTML pages at the repo root (`index.html`, `services.html`, …) plus `styles.css` and `app.js`
- Backend: dependency-free Python HTTP API in `server.py` (port **8000**)
- Database: SQLite file created automatically as `fitness_gurukul.sqlite3` (gitignored)
- Owner tools: `/admin` and `owner-data.html` (require `ADMIN_TOKEN`)

The old Node/Express server is deprecated. Use Python only.

## Run locally

```bash
cp .env.example .env
# set ADMIN_TOKEN to a long random string
python3 server.py
```

Or:

```bash
npm start
```

Open:

```text
http://127.0.0.1:8000
```

Office dashboard (DB-connected internal file):

```text
http://127.0.0.1:8000/office
```

Legacy admin / owner viewers:

```text
http://127.0.0.1:8000/admin
http://127.0.0.1:8000/owner-data.html
```

By default the server binds to `127.0.0.1`. To share on the same Wi-Fi:

```bash
HOST=0.0.0.0 python3 server.py
```

Then open `http://YOUR-LAPTOP-IP:8000` on another device. Admin APIs still require `ADMIN_TOKEN`.

## Environment

Copy `.env.example` to `.env`:

```text
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.6
ADMIN_TOKEN=replace-with-a-long-random-string
HOST=127.0.0.1
PORT=8000
```

- Without `OPENAI_API_KEY`, the chat widget answers from local website facts.
- Without `ADMIN_TOKEN` in `.env`, the server generates a temporary token for that process and prints it on startup.

## Pages

- `index.html` — home
- `about.html` — brand story
- `services.html` — plans and services
- `coaches.html` — coach directory
- `events.html` — corporate and community events
- `testimonials.html` — client stories
- `tools.html` — fitness calculators
- `contact.html` / `book-consultation.html` — lead forms
- `admin.html` — protected submissions dashboard
- `owner-data.html` — protected SQLite viewer

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

Office UI (`/office` → `office.html`) reads the live SQLite database and lets staff search leads, update status, export CSV, and delete records.

Sensitive paths (`.env`, `*.sqlite3`, `data/`, `server.py`, etc.) are not served as static files.

## Security notes

- Do not commit `.env`, `*.sqlite3`, or `data/*.json`
- Never share `/admin` or `owner-data.html` without the token
- Prefer localhost bind unless you intentionally need LAN access
