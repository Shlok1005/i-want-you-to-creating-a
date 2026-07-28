# Fitness Gurukul Full-Stack Website

Multi-page Fitness Gurukul website with a responsive frontend, Python backend, and SQLite database.

## What is included

- Frontend: detailed pages in `public/`
- Backend: dependency-free Python HTTP API in `server.py`
- Database: SQLite file created automatically as `fitness_gurukul.sqlite3`
- Dashboard: view user-entered leads, progress check-ins, and newsletter entries
- Download: packaged project ZIP at `public/fitness-gurukul-fullstack.zip`

## Pages

- `index.html` - logo-led home, guide, featured services, story, events, testimonials
- `programs.html` - detailed services, filters, comparison table, packages
- `events.html` - corporate marathon, cycling, active day, and planning flow
- `community.html` - community runs, cycling crews, wellness challenges, and transformation paths
- `coaches.html` - coaches, specialties, standards, testimonials, updates
- `tools.html` - BMI, goal recommendation, check-ins, storage mode status
- `contact.html` - consultation form, contact cards, areas, FAQ, newsletter
- `owner-data.html` - direct owner-only data viewer, not linked in the client navigation

## Brand system

The UI uses the uploaded Fitness Gurukul logo colors only:

- Black/dark background
- Logo cyan and blue
- Fitness red
- White/ice text surfaces

The fonts are Montserrat for headings/buttons and Inter for body/UI text.

## Run locally

```bash
python server.py
```

Open:

```text
http://127.0.0.1:8000
```

To collect form data from another laptop on the same Wi-Fi, share your main laptop's network link:

```text
http://YOUR-LAPTOP-IP:8000/contact.html
```

Do not share `127.0.0.1` with another device. On another laptop, `127.0.0.1` points back to that other laptop.

## Where user data appears

Run the backend, submit a form, then open:

```text
http://127.0.0.1:8000/owner-data.html
```

The raw JSON is available at:

```text
http://127.0.0.1:8000/api/admin-data
```

Static hosting cannot run Python or SQLite, so static forms save demo records in the browser only.

## AI chatbot (free by default)

The chat widget works **without any paid API**.

### Option A — Free FAQ assistant (zero setup)

Just run the server. The bot answers from Fitness Gurukul plan/coach facts.

```bash
npm start
# or: python server.py
```

### Option B — Free real AI with Ollama (recommended)

1. Install [Ollama](https://ollama.com)
2. Pull a small model:

```bash
ollama pull llama3.2
```

3. Restart the site server. It auto-detects Ollama at `http://127.0.0.1:11434`.

Optional `.env`:

```text
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
```

### Option C — Paid OpenAI (opt-in only)

OpenAI is **not** used by default, even if a key exists. To enable it:

```text
CHAT_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-5.6
```

Or keep `CHAT_PROVIDER=auto` and set `CHAT_ALLOW_OPENAI=true`.

Priority with `CHAT_PROVIDER=auto`: **Ollama → local FAQ** (OpenAI only when opted in).

## API endpoints

- `GET /api/health`
- `GET /api/content`
- `GET /api/chat/status`
- `POST /api/chat`
- `POST /api/leads`
- `GET /api/leads`
- `POST /api/newsletter`
- `POST /api/checkins`
- `GET /api/stats`
- `GET /api/admin-data`
