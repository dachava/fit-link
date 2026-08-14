# fit-link

A FastAPI app with two unrelated things sharing one Postgres database:

1. **Workout logger** — the original app. Multi-user, JWT-authenticated CRUD
   under `/auth` and `/workouts`.
2. **Exercise/routine reference library** — a read-only lookup tool: browse
   the exercise library, view routines with supersets/circuits rendered as
   grouped blocks, and read setup/execution/cue text per exercise. Single-user,
   server-rendered Jinja2 + HTMX, no auth in the app layer (meant to sit
   behind Cloudflare Access at the proxy in production).

The two don't cross-wire — see `CLAUDE.md` for the full split and the
conventions to follow when touching either side. The design brief, data
model, and phase plan live in `docs/fit-link-spec.md`.

## Quickstart (Docker Compose)

```
cp .env.example .env   # fill in SECRET_KEY, POSTGRES_* — see comments in the file
make up                # builds the api image, starts api + postgres
make migrate
make seed               # loads content/ into the DB, safe to re-run
```

Visit `http://localhost:8080`. `make logs` tails both services; `make down`
stops them.

Deploying for real (Cloudflare Tunnel, Access, backups) is covered in
`docs/deploy.md`; `make deploy` runs the full stack including the tunnel.

## Local dev without Docker

```
python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

Needs a reachable Postgres — either the one from `make up` (exposed on
`127.0.0.1:8080` only, not 5432, so use a separate instance) or a throwaway
container:

```
docker run -d --name fitlink-pg-tmp -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=fitlink -p 5432:5432 postgres:16-alpine
```

Then, with `DATABASE_URL`/`SECRET_KEY` set in `.env`:

```
.venv/bin/alembic upgrade head
.venv/bin/python -m app.content.load
.venv/bin/uvicorn app.main:app --reload
```

## Content pipeline

Exercise (`content/exercises/*.md`, YAML frontmatter + markdown body) and
routine (`content/routines/*.yaml`) files are the source of truth for the
reference library. `python -m app.content.load` validates everything
(reporting every error, not just the first) and upserts into the DB —
idempotent, safe to re-run after editing content or pulling changes.

## Offline support

The reference UI registers a service worker (`app/static/js/sw.js`) that
caches visited routine/exercise pages, so a routine you've already opened
still renders with a dead gym wifi signal. First-ever visit to an
unvisited page while offline falls back to `/offline`.

## Testing

No test suite yet. Planned: pytest with a Postgres fixture, covering at
minimum the content loader and the superset/circuit rendering path (see
`docs/fit-link-spec.md` §11).

## Project layout

```
app/
  models/        user.py, workout.py, exercise.py (logger) · library.py (reference library)
  routers/       auth, workouts, exercises (JWT API) · pages (reference UI, unauthenticated)
  content/       loader + Pydantic schemas + markdown renderer for the reference library
  templates/     Jinja2 templates for the reference UI
  static/        hand-written CSS, vendored htmx, PWA manifest/icons, service worker
alembic/         migrations
content/         exercise/routine source files loaded by app/content/load.py
scripts/         backup.sh (pg_dump, cron-able)
docs/            fit-link-spec.md (design brief) · deploy.md (Cloudflare Tunnel + Access setup)
```
