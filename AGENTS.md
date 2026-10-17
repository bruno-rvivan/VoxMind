# AGENTS.md

## Project overview

VoxMind is a small full-stack app for speech analysis. The backend is a FastAPI service in `backend/`, the frontend lives in `frontend/`, and the database is Postgres managed by `docker-compose.yml`.

The project is intentionally modular: route handlers are thin, business rules live in services/pipelines, and data models are defined separately from request/response schemas.

## Primary directories

- `backend/app/main.py` — FastAPI app bootstrap and router registration.
- `backend/app/api/v1/` — route modules, grouped by domain (`auth`, `users`, `analyses`).
- `backend/app/core/` — runtime settings, JWT/security helpers, and logging.
- `backend/app/db/` — database base/session config.
- `backend/app/models/` — SQLAlchemy ORM models.
- `backend/app/schemas/` — Pydantic request and response models.
- `backend/app/services/` — business logic used by endpoints.
- `backend/app/pipelines/` — analysis/transcription processing logic.
- `backend/tests/` — backend regression tests.
- `frontend/src/` — React frontend pages, components, and services.

## Local workflow

1. Start Postgres if it is not already running:
   `docker compose up -d db`
2. From `backend/`, use a local `.env` with at least:
   - `DATABASE_URL=postgresql+psycopg://voxmind:voxmind@localhost:5432/voxmind`
   - `JWT_SECRET_KEY=<at least 32 random characters>`
3. Run targeted backend tests with:
   `cd backend && pytest`

For API work, prefer focused test runs to validate the changed behavior instead of broad suites unless needed.

## Conventions to follow

- Keep backend endpoints in `app.api.v1.*` and use consistent router prefixes such as `/api/v1/...`.
- Keep route functions thin; push logic into `services/` or `pipelines/`.
- Keep schema validation in `app/schemas/`; do not duplicate or bypass Pydantic models.
- Keep SQLAlchemy models in `app/models/` and avoid ad hoc DB logic in the API layer.
- Preserve the existing naming style and domain structure instead of introducing a new architectural pattern for a small patch.
- Prefer small, reviewable edits over broad refactors.

## Coding expectations for AI agents

- Start by reading the closest existing module before changing it.
- Match the surrounding patterns in imports, router registration, naming, and error handling.
- When fixing a bug, reproduce it with a failing test first if the codebase already has a nearby test pattern.
- Prefer explicit, minimal changes and validate the smallest relevant command after each fix.
- Explain assumptions and trade-offs briefly when the change is non-obvious.
- If the requirement is ambiguous, ask a clarifying question before making a bigger change.

## Learning-first guidance

This project is a good place to learn while coding: prefer understanding before editing, verify each hypothesis with a small test or check, and keep the feedback loop short.

Treat every patch as an opportunity to learn the system, not just to make it pass. Read adjacent files, understand the data flow, and keep the implementation aligned with the repo’s existing architecture.

## Common pitfalls

- The backend expects a valid `JWT_SECRET_KEY` in environment configuration.
- The default local database URL points to `localhost:5432` and requires the Postgres container to be running.
- A lot of logic is intentionally split between `schemas`, `services`, and `pipelines`; placing business rules in the wrong layer makes the code harder to maintain.
- Frontend and backend are separate concerns in this repo; do not assume the frontend config is available in the Python backend.
