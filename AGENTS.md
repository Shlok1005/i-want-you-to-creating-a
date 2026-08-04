# AGENTS.md

## Cursor Cloud specific instructions

This repo is a Fitness Gurukul website: a static multi-page frontend plus a small backend that stores leads/newsletter/check-ins in SQLite and answers a chat widget.

### Services / how to run

- Primary dev server: `node server.js` (this is what `npm start` and `render.yaml` use). Serves the static site and the API on `http://localhost:3000` (override with `PORT`). Data is stored in `fitness_gurukul.sqlite3`, which is git-ignored and created automatically on first run.
- Alternative backend: `python server.py` (dependency-free, uses only the Python stdlib) serves the same site + API on port 8000. No `pip install` is needed. Use `node server.js` for normal development; the two servers are interchangeable implementations, not run together.
- Static deploy bundle (Netlify/Vercel): `bash scripts/prepare-static-dist.sh` builds `dist/` (frontend only, backend files stripped). This is a deploy artifact, not a dev server.
- Admin/data views (Node server): `/admin` (dashboard UI) and `/api/submissions` (JSON). `owner-data.html` is an unlinked owner-only viewer.

### Non-obvious caveats

- No lint and no automated tests are configured. `npm test` fails with "Missing script: test" and there is no `build` script. The GitHub Actions workflow (`.github/workflows/node.js.yml`) runs `npm test`, so CI is expected to fail on that step until a test script is added — this is pre-existing, not caused by setup.
- Lead submissions (`POST /api/submit`) try to forward to a Google Apps Script and to FormSubmit for email. These outbound calls fail gracefully when there is no network/credentials; the SQLite insert still succeeds and the API returns `ok: true` with `google_script:false, emailed:false`. So lead capture works fully offline.
- The chat widget (`/api/chat`) is free by default and answers from a local FAQ engine. Ollama (`http://127.0.0.1:11434`) and OpenAI are optional and opt-in only via env vars (see `README.md` / `.env.example`); nothing extra needs to run for chat to work.
- `.env` is optional. `server.js` loads it if present; all values have sensible defaults.

See `README.md` for the full endpoint list, chat provider options, and env var reference.
