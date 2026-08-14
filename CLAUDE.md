# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

fit-link is a FastAPI app that currently contains **two unrelated schemas sharing one Postgres database**:

1. **Workout logger** (`app/models/user.py`, `app/models/workout.py`, `app/models/exercise.py`) — the
   original app. Multi-user, JWT-authenticated CRUD (`/auth`, `/workouts`, `/workouts/{id}/exercises`).
   `Exercise` here is a *logged set/rep entry* belonging to a user's `Workout` (free-text `name`, int
   `sets`/`reps`, `weight_kg`, table `exercises`).
2. **Exercise/routine reference library** (`app/models/library.py`) — a read-only lookup tool being built
   per `docs/fit-link-spec.md`. Single-user, no auth in the app layer (meant to sit behind Cloudflare
   Access at the proxy). `LibraryExercise` here is a *shared reference entry* (setup/execution markdown,
   cues, muscle/equipment taxonomy, table `library_exercises`) — deliberately not named `Exercise` and not
   sharing a table with the logger's `Exercise`, since the two are unrelated concepts that happen to share
   an English word.

When working on either side, don't cross-wire them: the logger's services/routers/schemas stay untouched
by library work, and vice versa. `docs/fit-link-spec.md` is the design brief for the library/UI side,
including the phase plan and acceptance criteria — read it before making architectural changes there.

## Commands

There is no Makefile, Docker Compose, or test suite yet (planned; see `docs/fit-link-spec.md` phases 4–5).

Install deps:
```
python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

Run the dev server (needs `DATABASE_URL` and `SECRET_KEY`, see `.env.example`):
```
.venv/bin/uvicorn app.main:app --reload
```

Run migrations:
```
.venv/bin/alembic upgrade head
.venv/bin/alembic revision --autogenerate -m "message"   # after model changes
.venv/bin/alembic check                                   # verify no drift between models and migrations
```

Load/refresh reference content from `content/` into the DB (safe to re-run):
```
.venv/bin/python -m app.content.load
```

There's no local Postgres running by default. For quick manual testing, spin up a throwaway container:
```
docker run -d --name fitlink-pg-tmp -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=fitlink -p 5432:5432 postgres:16-alpine
```

## Architecture

**Content pipeline** (`app/content/`): `content/exercises/*.md` (YAML frontmatter + markdown body with
`## Setup`/`## Execution` sections) and `content/routines/*.yaml` are the source of truth for library
data, validated by `app/content/schemas.py` (Pydantic) and loaded via `app/content/load.py`. The loader
validates *everything* before writing anything and reports all errors at once, not just the first. It
upserts exercises in place by slug but **rebuilds each routine's block/exercise structure from scratch on
every run** (delete old blocks, reinsert from the content file) rather than diffing — simpler and
guarantees the nested superset/circuit structure can't drift from disk. `app/content/render.py` renders
markdown server-side for the UI; nothing ships a markdown parser to the browser.

**Async SQLAlchemy gotcha**: touching a relationship collection (e.g. `routine.blocks.append(...)`) after
a `flush()` triggers an implicit lazy load, which `AsyncSession` cannot service on plain attribute access
outside an `await` — it raises `MissingGreenlet`. The content loader avoids this entirely by working
through explicit FK ids and `db.add()`/`delete()` instead of relationship-collection mutation. Keep this
pattern for similar bulk/rebuild write paths.

**Reference UI** (`app/routers/pages.py`, `app/templates/`, `app/static/`): server-rendered Jinja2 +
HTMX, no JS build step, no client-side search — `/exercises` filtering hits the server and swaps in a
partial (`_exercise_list.html`) when the request carries the `HX-Request` header, otherwise renders the
full page. htmx is vendored into `app/static/js/` rather than loaded from a CDN, so the app stays a single
self-contained deployable. Routine blocks render as plain cards for `kind=single`, and as a visually
bracketed unit with the round count for `kind=superset`/`circuit` (`.block-superset`/`.block-circuit` in
`app/static/css/style.css`) — this bracketing is a hard requirement, not a style preference.

**Config** (`app/config.py`): `pydantic-settings` `BaseSettings` reads `.env` and rejects unrecognized
env vars by default (`extra_forbidden`) — adding a new setting means adding it to `Settings` before it can
appear in `.env`, or startup will fail validation.

**Auth split**: `/auth`, `/workouts`, `/workouts/{id}/exercises` require a JWT (`app/dependencies.py:
get_current_user`). Everything under `app/routers/pages.py` (the library/routine UI) is unauthenticated by
design — see the reference-library note above.
