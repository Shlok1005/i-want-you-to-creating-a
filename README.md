# Fitness Gurukul Website

Multi-page Fitness Gurukul site with a responsive frontend, Node/Python backends, SQLite lead storage, and an SEO-focused blog.

> **Full code documentation:** see [`DOCUMENTATION.md`](./DOCUMENTATION.md) for architecture, APIs, lead flow, chatbot, deployment, and file-by-file details.

## What is included

- Frontend: multi-page HTML/CSS/JS site (`index.html`, `services.html`, `blog.html`, etc.)
- Blog: 40 SEO articles from `topic 1`–`topic 4`, plus placeholder slots for future posts
- Backend: `node server.js` (primary) or dependency-free `python server.py`
- Database: SQLite file created automatically as `fitness_gurukul.sqlite3`
- Admin: `/admin` and `/api/submissions` (Node); `owner-data.html` for owner-only viewing

## Pages

| Page | Purpose |
|------|---------|
| `index.html` | Home — hero, programs, app promo, blog teaser |
| `services.html` | Training programs and plans |
| `coaches.html` | Coach directory (+ `/coaches/*.html` profiles) |
| `events.html` | Community events and registration |
| `blog.html` | Blog explore hub (categories, search, placeholders) |
| `blog/*.html` | Individual SEO blog articles |
| `testimonials.html` | Member stories |
| `tools.html` | BMI, BMR, body fat, macro calculators |
| `transformation-challenge.html` | 90-day challenge |
| `about.html` | Founder & story |
| `contact.html` / `book-consultation.html` | Lead capture |
| `owner-data.html` | Unlinked owner data viewer |

## Blog & SEO

Content sources (kept in repo for regeneration):

- `topic 1/` — Strength & Training (docx)
- `topic 2/` — Group Fitness (docx)
- `topic 3/` — Kids Fitness (docx)
- `topic 4/` — Race & Endurance (markdown)

Published output:

- `blog.html` — Fitelo-style explore page with filters and “coming soon” placeholders
- `blog/*.html` — articles with meta description, Open Graph, JSON-LD `BlogPosting` + breadcrumbs
- Footer SEO directory — all blog links + popular search keywords **below the footer** on every public page (static HTML + runtime injector)
- `sitemap.xml` / `robots.txt` — search discovery
- `blog/posts.json` / `blog/seo-groups.json` — metadata for filters and footer links

Regenerate articles after editing topic folders:

```bash
python3 scripts/generate-blog.py
```

## Run locally

Primary (Node, port 3000):

```bash
npm install
npm start
```

Open `http://localhost:3000`

Alternative (Python stdlib only, port 8000):

```bash
python server.py
```

Open `http://127.0.0.1:8000`

Do not run both servers together. For LAN testing use your machine IP, not `127.0.0.1`, on other devices.

## AI chatbot (free by default)

The chat widget works **without any paid API**.

### Option A — Free FAQ assistant (zero setup)

```bash
npm start
# or: python server.py
```

### Option B — Free real AI with Ollama

1. Install [Ollama](https://ollama.com)
2. `ollama pull llama3.2`
3. Restart the site server (auto-detects `http://127.0.0.1:11434`)

Optional `.env`:

```text
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
```

### Option C — Paid OpenAI (opt-in only)

```text
CHAT_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-5.6
```

Or `CHAT_PROVIDER=auto` with `CHAT_ALLOW_OPENAI=true`.

Priority with `CHAT_PROVIDER=auto`: **Ollama → local FAQ** (OpenAI only when opted in).

## API endpoints

- `GET /api/health`
- `GET /api/content`
- `GET /api/chat/status`
- `POST /api/chat`
- `POST /api/submit` (leads)
- `POST /api/leads`
- `GET /api/leads`
- `POST /api/newsletter`
- `POST /api/checkins`
- `GET /api/stats`
- `GET /api/admin-data` / `GET /api/submissions`

Lead submit still succeeds offline (SQLite); Google Apps Script / FormSubmit forwarding fails gracefully when credentials/network are missing.

## Deploy

- **Node host (e.g. Render):** `npm start` via `render.yaml`
- **Static (Netlify/Vercel):** `bash scripts/prepare-static-dist.sh` builds `dist/` (frontend only)

## Brand system

- Dark background with cyan/amber accents
- Logo-led header; Public Sans UI type
- Prefer existing site patterns when extending pages
