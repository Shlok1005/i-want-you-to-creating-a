# Fitness Gurukul — Code Documentation

Detailed technical documentation of the Fitness Gurukul website codebase: architecture, technologies, files, APIs, data flows, and deployment.

---

## Table of contents

1. [Project overview](#1-project-overview)
2. [Tech stack & what is used](#2-tech-stack--what-is-used)
3. [Repository structure](#3-repository-structure)
4. [Architecture](#4-architecture)
5. [Frontend](#5-frontend)
6. [Backend (Node — primary)](#6-backend-node--primary)
7. [Backend (Python — alternate)](#7-backend-python--alternate)
8. [Lead capture system](#8-lead-capture-system)
9. [Chatbot](#9-chatbot)
10. [Database schemas](#10-database-schemas)
11. [API reference](#11-api-reference)
12. [Pages inventory](#12-pages-inventory)
13. [Assets & media](#13-assets--media)
14. [Environment variables](#14-environment-variables)
15. [Scripts & tests](#15-scripts--tests)
16. [Deployment](#16-deployment)
17. [localStorage keys](#17-localstorage-keys)
18. [Brand / design system](#18-brand--design-system)
19. [Key function index](#19-key-function-index)
20. [Known caveats](#20-known-caveats)

---

## 1. Project overview

Fitness Gurukul is a **multi-page marketing website** for a Hyderabad-based fitness brand (personal training, yoga, endurance, corporate events, 90-day challenge).

The product includes:

- Public marketing pages (home, services, coaches, events, testimonials, tools, challenge, contact)
- Lead capture (consultation, challenge, corporate) → Google Sheets + email
- Optional local SQLite storage when a Node/Python server is running
- Free FAQ chatbot (optional Ollama / opt-in OpenAI)
- Owner/admin views for stored submissions

There is **no SPA framework**. Pages are plain HTML + one shared `app.js` + one shared `styles.css`.

---

## 2. Tech stack & what is used

### Frontend

| Technology | Where / why |
|------------|-------------|
| HTML5 | All pages (`*.html`, `coaches/*.html`) |
| CSS3 | `styles.css` — design system, layouts, responsive rules |
| Vanilla JavaScript (ES modules not used) | `app.js` — rendering, forms, chat, carousels |
| Google Fonts (Public Sans) | Loaded from HTML pages |
| Netlify Forms attributes | `data-netlify="true"` for deploy-time form detection |
| FormSubmit.co | Browser + server email backup for leads |
| Google Apps Script | Primary lead sink (Sheet row + `MailApp`) |
| localStorage | Offline lead copies, calculator history, auth stubs |

### Backend (Node — primary)

| Package | Version (package.json) | Purpose |
|---------|------------------------|---------|
| `express` | ^4.18.2 | HTTP server, static files, routes |
| `cors` | ^2.8.5 | Cross-origin API access |
| `sql.js` | ^1.11.0 | SQLite in WASM (file: `fitness_gurukul.sqlite3`) |
| Node.js built-ins | `fs`, `path`, `fetch` | Env loading, DB file I/O, outbound HTTP |

Entry: `server.js` · Scripts: `npm start` / `npm run dev` → `node server.js` · Default port: **3000**

### Backend (Python — alternate)

| Technology | Purpose |
|------------|---------|
| Python 3 stdlib only | `http.server`, `sqlite3`, `json`, `urllib` |
| `requirements.txt` | Empty marker — **no pip packages required** |

Entry: `server.py` · Default port: **8000**

### Serverless / integrations

| Piece | Purpose |
|-------|---------|
| `api/submit.js` | Vercel serverless `POST /api/submit` |
| `netlify/functions/submit.ts` | Netlify Function mapped to `/api/submit` |
| `netlify/functions/_shared/lead-mail.ts` | Shared FormSubmit helper |
| `google-apps-script/Code.gs` | Sheet tabs + email for leads |

### Hosting / CI

| Config | Target |
|--------|--------|
| `render.yaml` | Render Node web service (`node server.js`) |
| `netlify.toml` | Static `dist/` + Netlify Function |
| `vercel.json` | Static `dist/` + Vercel API route |
| `.github/workflows/node.js.yml` | CI: install, build dist, syntax check, smoke test |
| `.github/workflows/deploy-vercel.yml` | Manual Vercel production deploy |

### Optional AI

| Provider | When used |
|----------|-----------|
| Local FAQ engine | Default (always works offline) |
| Ollama (`llama3.2`) | If running at `http://127.0.0.1:11434` and `CHAT_PROVIDER=auto|ollama` |
| OpenAI | Only if opted in (`CHAT_PROVIDER=openai` or `CHAT_ALLOW_OPENAI=true` + `OPENAI_API_KEY`) |

---

## 3. Repository structure

```text
.
├── index.html, about.html, services.html, coaches.html, events.html,
│   testimonials.html, tools.html, contact.html, book-consultation.html,
│   transformation-challenge.html, admin.html, owner-data.html, __forms.html
├── app.js                 # Shared frontend runtime (~3.4k lines)
├── styles.css             # Global design system
├── server.js              # Primary Node/Express API + static host
├── server.py              # Alternate Python stdlib API + static host
├── package.json           # Node deps & scripts
├── requirements.txt       # Python marker (stdlib only)
├── .env.example           # Env template
├── api/submit.js          # Vercel serverless lead endpoint
├── netlify/
│   ├── functions/submit.ts
│   └── functions/_shared/lead-mail.ts
├── google-apps-script/Code.gs
├── scripts/
│   ├── prepare-static-dist.sh
│   └── smoke-leads.sh
├── coaches/*.html         # Individual coach profile pages
├── assets/                # Logos, hero art, coach photos, CDN mirrors
├── gallery/               # Event / about photo sets
├── services/              # Plan artwork (fg-core, fg-prime, …)
├── screens/               # App store screenshots
├── testimonials/          # Video testimonials (mp4)
├── index/                 # Home section media (services, story-map, testi)
├── story map/             # Story map frames (folder name has a space)
├── new-ind/               # Extra event image
├── DOCUMENTATION.md       # This file
├── README.md              # Quick start
└── AGENTS.md              # Cursor Cloud agent notes
```

---

## 4. Architecture

Three hosting modes share the same frontend:

```text
┌─────────────────────────────────────────────────────────────┐
│  Browser (HTML + app.js + styles.css)                       │
│  - Renders pages from embedded realData or /api/content     │
│  - Leads: Google Apps Script GET → FormSubmit → localStorage│
│  - Chat: /api/chat if backend detected, else local FAQ      │
└───────────────┬─────────────────────────────┬───────────────┘
                │                             │
     Long-running server              Static + serverless
     ┌──────────┴──────────┐         ┌────────┴────────┐
     │ Node server.js :3000│         │ Netlify / Vercel│
     │ or Python :8000     │         │ dist/ + /api/submit
     │ SQLite + chat API   │         │ No SQLite/chat  │
     └─────────────────────┘         └─────────────────┘
                │
                ▼
     Google Apps Script → Google Sheet tabs + MailApp emails
```

| Mode | Persistence | Lead path | Chat |
|------|-------------|-----------|------|
| **Node** (`npm start`) | `submissions` in SQLite via sql.js | Browser Apps Script **and/or** `POST /api/submit` | Local / Ollama / OpenAI |
| **Python** (`python server.py`) | Multi-table SQLite | `POST /api/leads` (SQLite only; no Sheets/FormSubmit in server) | Same providers; persists chat |
| **Static (Netlify/Vercel)** | None on host | Browser Apps Script + FormSubmit; optional function `POST /api/submit` | Local FAQ only in browser |

Do **not** run Node and Python together expecting one shared schema — their databases differ.

---

## 5. Frontend

### Boot sequence (`app.js` → `boot()`)

1. `initPlanModals()` and seed `renderServices(realData.services)`
2. `detectBackend()` → `GET /api/health` → sets `usesLocalBackend`
3. `loadContent()` → `GET /api/content` (falls back to embedded `realData`)
4. Render services, coaches, testimonials, updates, areas, workouts, contact
5. Wire UI: carousels, reveals, coach/book modals, forms, nav, event banner, footer, WhatsApp float, chatbot, site popup

### Media fallback

If an `img` / `video` / `source` fails to load, `app.js` rewrites the path to:

`https://media.githubusercontent.com/media/saikrishnacoder/i-want-you-to-creating-a/main/<path>`

### Important client API usage

| Call | Used by | Notes |
|------|---------|-------|
| `GET /api/health` | `detectBackend()` | Enables server-backed chat |
| `GET /api/content` | `loadContent()` | Optional CMS-like payload |
| `GET /api/chat/status` | Chat widget | Engine + suggestions |
| `POST /api/chat` | Chat widget | Only if backend detected |
| `GET /api/admin-data` | `owner-data.html` / `refreshAdminData()` | **Python** |
| `POST /api/calculations` | `tools.html` | **Python** |
| `GET /api/submissions` | `admin.html` | **Node** |
| `DELETE /api/submissions/:id` | `admin.html` | **Node** |
| Apps Script GET | `postLeadToGoogleScript()` | **Primary lead path** |
| FormSubmit AJAX | `emailLeadViaFormSubmit()` | Email backup |

Marketing lead forms do **not** call `POST /api/submit` from the browser. That endpoint exists for Node and serverless hosts; the browser path is Apps Script + FormSubmit via `submitLead()`.

### Embedded data (`realData` in `app.js`)

- **Services**: `name`, `tag`, `category` (`core` \| `prime` \| `signature` \| `endurance` \| `forge` \| `elite`), `summary`, `price`, `accent`, `points[]`, `sessions`, `link`
- **Coaches**: `name`, `role`, `slug`, `category`, `bio`, `focus[]`, `highlight`, `color`, `image`
- **Testimonials**: `name`, `quote`, `result`, `rating`, gallery/before/after fields, `journey[]`, `coach`
- **Contact**: phone, WhatsApp, email, address (Manikonda, Hyderabad)

### Forms wired by `wireForms()` / binders

| Form ID | `form_type` | Page |
|---------|-------------|------|
| `#leadForm` | `consultation` | `contact.html` |
| `#consultPageForm` | `consultation` | `book-consultation.html` |
| `#challengeLeadForm` | `transformation_challenge` | `transformation-challenge.html` |
| `#bookModalForm` / coach inline forms | `consultation` | Modals / coach cards |
| `#corpEventForm` | `corporate_event` | `events.html` |

Global export: `window.fgSubmitLead`, `window.FG_GOOGLE_SCRIPT_URL`, `window.FG_LEAD_NOTIFY_EMAILS`.

### Tools page (`tools.html`)

Client-side calculators (not in `app.js`):

| Slug | Calculator |
|------|------------|
| `bmi` | Body Mass Index |
| `1rm` | One-rep max (Epley) |
| `tdee` | TDEE (Mifflin-St Jeor) |
| `bodyfat` | Body fat % from BMI |
| `ideal-weight` | Ideal weight (Devine) |
| `lean-body-mass` | Lean body mass |
| `protein` | Daily protein |
| `macro` | Macro split |
| `whr` | Waist-to-hip ratio |
| `max-hr` | Max heart rate |
| `sleep` | Sleep calculator |
| `bmd` | Bone health risk |

Results save to `localStorage["fg_calculator_results"]` (max 50) and best-effort `POST /api/calculations` when Python backend is present.

### Chat widget (`injectSiteChatbot()`)

- Session id: `fg-<timestamp>-<random>`
- If `usesLocalBackend`: `POST /api/chat` with `{ message, history, sessionId }`
- Else: `localChatReply()` keyword FAQ over `realData.services`
- Suggestions rendered from `/api/chat/status` or defaults

---

## 6. Backend (Node — primary)

**File:** `server.js`

### Middleware

- `cors()`
- `express.json()`
- `express.urlencoded({ extended: true })`
- `express.static(__dirname)` — serves the whole site from the repo root

### Core helpers

| Function | Role |
|----------|------|
| `loadEnvFile()` | Loads `.env` without overwriting existing env |
| `initDatabase()` / `saveDatabase()` | sql.js open/create + persist file |
| `insertSubmission()` / `readSubmissions()` / `deleteSubmission()` | CRUD for `submissions` |
| `notifyLeadChannels()` | Apps Script then FormSubmit |
| `forwardLeadToGoogleScript()` | GET `?write=1&...` |
| `emailLeadViaFormSubmit()` | POST to FormSubmit for each notify email |
| `resolveChatEngine()` / `generateChatReply()` | Provider selection + reply |
| `generateLocalChatReply()` / `planScore()` / `findMatchingPlans()` | Offline FAQ |
| `callOllamaChat()` / `callOpenAIChat()` | Optional AI |

### Routes

| Method | Path | Behavior |
|--------|------|----------|
| `GET` | `/` | `index.html` |
| `GET` | `/admin` | `admin.html` |
| `GET` | `/api/health` | `{ ok, engine: "node", aiEnabled, chatEngine, free }` |
| `GET` | `/api/content` | `{ ok, plans, contact }` |
| `GET` | `/api/chat/status` | Engine, model, free flag, suggestions |
| `POST` | `/api/chat` | Chat reply (max message length 2000) |
| `POST` | `/api/submit` | Validate → SQLite → notify channels |
| `GET` | `/api/submissions` | All rows (no auth) |
| `DELETE` | `/api/submissions/:id` | Delete one row |

### `POST /api/submit` validation

- Consultation: requires `name`, `phone`, `program`, `goal`
- Corporate (`form_type === "corporate_event"`): requires `company`, `contact_name`, `email`, `phone`, `event_type`, `attendees`

Success shape:

```json
{ "ok": true, "id": "<id>", "google_script": true, "emailed": false }
```

SQLite insert succeeds even if outbound notify fails.

---

## 7. Backend (Python — alternate)

**File:** `server.py` · Class: `AppHandler(SimpleHTTPRequestHandler)`

### Differences from Node

| Topic | Node | Python |
|-------|------|--------|
| Port | 3000 | 8000 |
| DB | Single `submissions` (sql.js) | Multi-table native `sqlite3` |
| Lead API | `/api/submit` + Sheets + FormSubmit | `/api/leads` SQLite only |
| Admin | `/admin`, `/api/submissions` | `/api/admin-data`, `owner-data.html` |
| Content | plans + contact | services, coaches, testimonials, updates, areas, contact |
| Chat persistence | none | `chat_messages` + `sessionId` |
| Calculators API | none | `POST /api/calculations` |
| Dependencies | express, cors, sql.js | stdlib only |

### Python routes (implemented)

| Method | Path | Notes |
|--------|------|-------|
| `GET` | `/api/health` | DB path + table list |
| `GET` | `/api/content` | Full content payload |
| `GET` | `/api/chat/status` | Same idea as Node |
| `POST` | `/api/chat` | Saves exchange via `save_chat_exchange` |
| `POST` | `/api/leads` | Requires name, phone, goal, program |
| `POST` | `/api/calculations` | Saves calculator result |
| `GET` | `/api/admin-data` | Last 50 rows per table |

Missing paths fall back to `/index.html`. SQLite files are not served for download.

> README historically listed `POST /api/newsletter`, `POST /api/checkins`, `GET /api/stats` — those handlers are **not** present in current `server.py` (tables may exist for future use).

---

## 8. Lead capture system

### Primary browser flow

```text
Form submit (preventDefault)
  → FormData → payload (+ form_type)
  → submitLead(payload)
       1. normalizeLeadPayload (requires name + phone)
       2. postLeadToGoogleScript  → GET Apps Script /exec?write=1&...
       3. emailLeadViaFormSubmit  → FormSubmit (best-effort, both inboxes)
       4. saveLeadLocally         → localStorage "fg_leads"
  → UI success/error status
```

Because Apps Script responses are often opaque to the browser (CORS/redirect), `postLeadToGoogleScript` treats a sent request as success and may retry with `mode: "no-cors"`.

### Google Apps Script (`google-apps-script/Code.gs`)

| Function | Role |
|----------|------|
| `doGet` / `doPost` | Web app entry |
| `handleLead_` | Validate, append row, email |
| `sheetTab_` | Route form type → sheet tab |
| `ensureHeader_` | Create header row |
| `sendLeadEmail_` | `MailApp` to both owner inboxes |
| `testSetup` | One-time permission grant |

**Sheet tabs:**

| `form_type` pattern | Tab |
|---------------------|-----|
| `challenge*` | `Challenge` |
| `corporate*` | `Corporate` |
| default | `Consultations` |

**Row columns:** Timestamp, Form Type, Name, Phone, Email, Program, Goal, Message, Coach, Company, Contact Name, Event Type, Attendees, Preferred Date, Budget, Location, Source.

**Notify emails:** `contact@fitnessgurukul.co.in`, `fitnessgurukul01@gmail.com`.

### Server / serverless path

`POST /api/submit` (Node, Vercel `api/submit.js`, Netlify `submit.ts`):

1. Validate payload  
2. (Node only) insert SQLite  
3. Forward GET to Apps Script  
4. FormSubmit if Apps Script did not email (or as backup)

Vercel/Netlify return **502** if both Google + FormSubmit fail. Node still returns `ok: true` after a successful SQLite write.

---

## 9. Chatbot

### Provider resolution (`CHAT_PROVIDER`)

| Value | Behavior |
|-------|----------|
| `local` | Always local FAQ |
| `ollama` or `auto` | Prefer Ollama if `/api/tags` is healthy |
| `openai` | Force OpenAI (needs key) |
| `auto` + OpenAI | OpenAI only if `CHAT_ALLOW_OPENAI=true` **and** `OPENAI_API_KEY` set |

**Default order for `auto`:** Ollama → OpenAI (opt-in only) → local FAQ.

Defaults:

- `OLLAMA_BASE_URL=http://127.0.0.1:11434`
- `OLLAMA_MODEL=llama3.2`
- OpenAI model default `gpt-5.6`
- Message max length: 2000
- History: last 8 turns
- Ollama status cached ~15 seconds

Local FAQ covers greetings, contact info, Core/Prime/Signature comparison, plan scoring, yoga/coach hints, events (Python FAQ is richer: coaches, services, booking, areas, app download).

---

## 10. Database schemas

### Node — table `submissions`

File: `fitness_gurukul.sqlite3` (git-ignored, created on first run).

| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PK | `Date.now().toString(36) + random` |
| `form_type` | TEXT | default `consultation` |
| `name`, `phone`, `email` | TEXT | |
| `program`, `goal`, `message`, `coach` | TEXT | |
| `company`, `contact_name`, `event_type` | TEXT | corporate |
| `attendees`, `preferred_date`, `budget`, `location` | TEXT | corporate |
| `timestamp` | TEXT | ISO |
| `ip` | TEXT | `x-forwarded-for` or socket |

Persistence: `db.export()` → `fs.writeFileSync`.

### Python — multi-table

| Table | Main columns |
|-------|----------------|
| `leads` | name, phone, goal, program, message, created_at |
| `newsletter` | email UNIQUE, created_at |
| `checkins` | name, weight, stamina, mood, created_at |
| `ai_scans` | name, focus, summary, coach_route, camera_used, created_at |
| `calculator_results` | calculator, title, result, unit, rating, created_at |
| `chat_messages` | session_id, role, content, source, created_at |

---

## 11. API reference

### Shared (Node + Python)

#### `GET /api/health`

Node example:

```json
{ "ok": true, "engine": "node", "aiEnabled": false, "chatEngine": "local", "free": true }
```

#### `GET /api/content`

- Node: `{ "ok": true, "plans": [...], "contact": {...} }`
- Python: services, plans, coaches, testimonials, updates, serviceAreas, contact

#### `GET /api/chat/status`

```json
{
  "ok": true,
  "aiEnabled": false,
  "engine": "local",
  "model": "local-faq",
  "free": true,
  "suggestions": ["Which plan is best for weight loss?", "..."]
}
```

#### `POST /api/chat`

Request:

```json
{ "message": "string", "history": [{ "role": "user", "content": "..." }], "sessionId": "optional" }
```

Response:

```json
{ "ok": true, "reply": "...", "source": "local|ollama|openai", "aiEnabled": false, "free": true, "suggestions": [] }
```

### Node-only

- `POST /api/submit` → `{ ok, id, google_script, emailed }`
- `GET /api/submissions` → `{ ok, count, data }`
- `DELETE /api/submissions/:id` → `{ ok: true }`

### Python-only

- `POST /api/leads` → 201 `{ ok, message }`
- `POST /api/calculations` → 201 `{ ok, message }`
- `GET /api/admin-data` → `{ leads, checkins, newsletter, ai_scans, calculations, chat_messages }`

### Serverless

- `POST /api/submit` (Vercel/Netlify) → `{ ok, google_script, emailed }` (no SQLite)

---

## 12. Pages inventory

### Public

| Page | Purpose |
|------|---------|
| `index.html` | Home — hero, services preview, story, coaches, app screens |
| `about.html` | Brand / founder (Ravi Miska) story |
| `services.html` | Plans, compare, FitBudd pay links |
| `coaches.html` | Coach directory + filters |
| `coaches/*.html` | 18 individual coach profiles |
| `events.html` | Rides, galleries, corporate form |
| `testimonials.html` | Quotes, story map, video testimonials |
| `tools.html` | Fitness calculators |
| `transformation-challenge.html` | 90-day challenge + lead form |
| `contact.html` | Consultation form + FAQ |
| `book-consultation.html` | Standalone booking form |

### Internal / helpers

| Page | Purpose |
|------|---------|
| `admin.html` | Node admin dashboard (`/api/submissions`) |
| `owner-data.html` | Python owner viewer (`/api/admin-data`) — not in main nav |
| `__forms.html` | Hidden Netlify form skeletons |

Shared chrome (injected by `app.js`): site header/nav patterns in HTML, runtime footer (`injectFooter`), WhatsApp float, chatbot, delayed consultation popup (~5 minutes).

---

## 13. Assets & media

| Path | Contents |
|------|----------|
| `assets/` | Logos, AI hero/event images |
| `assets/cdn/` | Mirrored CDN-style media |
| `assets/coaches/` | Coach headshots |
| `gallery/april-ride/`, `may-ride/` | Ride photo sets |
| `gallery/born-stars/` | Born Stars images |
| `gallery/about-us/` | Founder photo |
| `services/` | Plan art (`fg-core.png`, `fg-prime.png`, …) |
| `screens/` | App screenshots (`img-1.png` … `img-8.png`) |
| `testimonials/` | MP4 videos (`neha.mp4`, etc.) |
| `index/services/`, `index/story-map/`, `index/testi/` | Home section media |
| `story map/` | Story map frames |
| Root PNGs | `udit.png`, `neha.png`, `deepak.png`, `ramakrishna.png` |

Netlify redirects map legacy asset URLs to these restored paths (see `netlify.toml`).

---

## 14. Environment variables

From `.env.example` and server code:

| Variable | Used by | Default / purpose |
|----------|---------|-------------------|
| `PORT` | Node / Python | `3000` / `8000` |
| `CHAT_PROVIDER` | both | `auto` \| `local` \| `ollama` \| `openai` |
| `OLLAMA_BASE_URL` | both | `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | both | `llama3.2` |
| `CHAT_ALLOW_OPENAI` | both | must be `true` to allow OpenAI under `auto` |
| `OPENAI_API_KEY` | both | Paid chat |
| `OPENAI_MODEL` | both | default `gpt-5.6` |
| `GOOGLE_SCRIPT_URL` | Node, Vercel, Netlify | Apps Script `/exec` URL |
| `FG_GOOGLE_SCRIPT_URL` | Node, Netlify | Alias |
| `LEAD_NOTIFY_EMAIL` | Node, Vercel | Comma-separated notify inboxes |
| `FG_LEAD_EMAIL` | Node | Alias |
| `FORMSUBMIT_DISABLE` | Node, Netlify | `1` disables FormSubmit |

`.env` is optional. Servers only set keys that are not already in the environment.

---

## 15. Scripts & tests

| Command | What it does |
|---------|----------------|
| `npm start` / `npm run dev` | `node server.js` |
| `npm test` | `node --check` on `app.js`, `api/submit.js`, `server.js` + `bash scripts/smoke-leads.sh` |
| `bash scripts/prepare-static-dist.sh` | Build `dist/` static bundle (strips backends) |
| `bash scripts/smoke-leads.sh` | Live curl of Apps Script GET write (needs network) |
| `python server.py` | Alternate full-stack server on port 8000 |

`prepare-static-dist.sh` excludes `server.js`, `server.py`, `package*.json`, `render.yaml`, `api/`, `netlify/`, `google-apps-script/`, etc. from `dist/`.

---

## 16. Deployment

### Local development (recommended)

```bash
npm install
npm start
# → http://127.0.0.1:3000
```

Or:

```bash
python server.py
# → http://127.0.0.1:8000
```

### Render

`render.yaml` → Node service, `npm install`, `node server.js`. Full API + SQLite (disk is ephemeral unless a persistent disk is attached).

### Netlify

1. Build: `bash scripts/prepare-static-dist.sh`
2. Publish: `dist/`
3. Function: `netlify/functions/submit.ts` → `/api/submit`
4. Asset redirects for legacy media paths

Leads still work via browser Apps Script even without the function.

### Vercel

1. Build: same `prepare-static-dist.sh` → `dist/`
2. Serverless: repo-root `api/submit.js`
3. Cache headers force revalidate for `app.js` and `*.html`

### Static-only note

Static hosting cannot run Python/Node SQLite. Forms still capture leads via Google Apps Script + FormSubmit + `localStorage`.

---

## 17. localStorage keys

| Key | Purpose |
|-----|---------|
| `fg_leads` | Local copies of submitted leads |
| `fg_users` | Client-side auth user list (stub) |
| `fg_session` | Current auth session (stub) |
| `fg_calculator_results` | Last 50 calculator results |

---

## 18. Brand / design system

From `:root` in `styles.css`:

- Backgrounds: black / near-black (`#000`, `#0a0a0a`, surfaces `#111` / `#1a1a1a`)
- Text: white / muted gray
- Accents: logo cyan/blue + fitness red (page-specific challenge green / WhatsApp `#25d366`)
- Radius: ~12px / 18px; soft heavy shadows
- Font: Public Sans (Google Fonts)
- Atmosphere: dark gradients, amber/cyan radials, grid overlay, hero `assets/ai-fitness-hero.png`
- Layout shells: `.page-shell`, `.section-shell`, `.site-header`, desktop/mobile nav
- Responsive breakpoints roughly 480–1020px; `prefers-reduced-motion` respected in places

---

## 19. Key function index

### `app.js` (frontend)

- Utils: `qs`, `qsa`, `api`, `detectBackend`, `loadContent`
- Render: `renderServices`, `renderCoaches`, `renderTestimonials`, `renderStoryMap`, `renderWorkoutGrid`, `renderContact`
- Leads: `normalizeLeadPayload`, `postLeadToGoogleScript`, `emailLeadViaFormSubmit`, `submitLead`, `saveLeadLocally`, `bindLeadForm`, `wireForms`
- Chrome: `injectFooter`, `injectWhatsAppFloat`, `injectSiteChatbot`, `injectLatestEventBanner`, `injectBookModal`
- Motion: `initHeroCarousel`, `initPlanModals`, `initTestiCarousel`, `initRevealAnimations`, `animateCounters`

### `server.js` (Node)

`loadEnvFile`, `initDatabase`, `insertSubmission`, `notifyLeadChannels`, `forwardLeadToGoogleScript`, `emailLeadViaFormSubmit`, `resolveChatEngine`, `generateChatReply`, `generateLocalChatReply`, `callOllamaChat`, `callOpenAIChat`

### `server.py` (Python)

`init_db`, `content_payload`, `AppHandler.do_GET` / `do_POST`, `resolve_chat_engine`, `generate_chat_reply`, `save_chat_exchange`, `find_matching_coaches`, `find_matching_services`, `find_matching_plans`

### Apps Script

`doGet`, `doPost`, `handleLead_`, `sheetTab_`, `sendLeadEmail_`, `testSetup`

---

## 20. Known caveats

1. **Two backends, different schemas** — Node uses `submissions`; Python uses multiple tables. Pick one for local admin views.
2. **Admin has no auth** — `/api/submissions` and `/api/admin-data` are unprotected; keep them off public production or add auth before exposing.
3. **Lead success can be optimistic in the browser** — CORS/opaque Apps Script responses are treated as success; email often still arrives.
4. **README vs code drift** — Some README Python endpoints (`newsletter`, `checkins`, `stats`) are not implemented yet.
5. **`workouts.html`** is linked from the injected footer but is not present in the repo.
6. **`AGENTS.md`** may lag `package.json` (e.g. `npm test` now exists).
7. **Static deploy strips backends** — chat API and SQLite admin only work with Node/Python/Render, not pure Netlify/Vercel static hosting.
8. **OpenAI is never used by default** — even if a key exists, you must opt in.

---

## Quick start cheat sheet

```bash
# Full stack (Node)
npm install && npm start
# open http://127.0.0.1:3000

# Full stack (Python)
python server.py
# open http://127.0.0.1:8000

# Static bundle for Netlify/Vercel
bash scripts/prepare-static-dist.sh

# Syntax + lead smoke test
npm test
```

Owner data views:

- Node: `http://127.0.0.1:3000/admin`
- Python: `http://127.0.0.1:8000/owner-data.html`

For day-to-day agent notes, see `AGENTS.md`. For a shorter intro, see `README.md`.
