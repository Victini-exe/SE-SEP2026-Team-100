# IITM BS Student Mentoring Platform

A React and FastAPI foundation for matching IIT Madras BS students with mentors. The repository currently implements authentication, profiles, mentor applications and review, search/recommendations, and a working mentoring lifecycle API with a connected role-based frontend workspace.

## Current implementation

- JWT authentication and role checks for students, mentors, and administrators.
- Institute email registration against configured exact domains.
- Student profiles and career questions; mentor applications and profiles.
- Administrator approval/rejection of mentor applications.
- Mentor search, explainable recommendations, and capacity-aware availability.
- Mentoring requests, withdrawal, seven-day lazy expiry, decisions, and relationship closure.
- Session proposals, time-zone conversion, messaging, session notes, notifications, and reports.
- Administrator user suspension/reactivation, moderation, analytics, and inactivity alerts.
- React registration/login and student, mentor, and administrator workspaces connected to the API.

This is an actively evolving milestone project, **not a production-ready service**. The frontend does not yet expose every backend capability, the admin analytics are limited, and full frontend/E2E test suites are not configured. See [the milestone checklist](docs/submission/MILESTONE_2_SUBMISSION_CHECKLIST.md) for verified gaps and deliverable status.

## Technology

- Frontend: React, TypeScript, Vite, React Router.
- Backend: FastAPI, SQLAlchemy 2, Pydantic, Alembic.
- Database: SQLite by default; migrations use portable relational types and constraints.
- Tests: pytest and FastAPI TestClient.

Tailwind CSS, React Hook Form, Zod, TanStack Query, Vitest, and Playwright are **not currently dependencies**. Avoid assuming they are part of the implemented stack.

## Prerequisites

- Python 3.10 or later (Python 3.13 verified).
- Node.js 22 or later and npm.
- PowerShell on Windows; equivalent shell commands can be used on other platforms.

## Local setup (Windows PowerShell)

From the repository root:

```powershell
py -3.13 -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt

Push-Location backend
$env:PYTHONPATH = "."
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
Pop-Location
```

In a second terminal:

```powershell
Push-Location frontend
npm ci
npm run dev -- --host localhost --port 5173
Pop-Location
```

Open `http://localhost:5173`. The configured backend CORS origin defaults to `http://localhost:5173`; use that hostname rather than `127.0.0.1` unless you change the configuration.

## Configuration and database

`backend/app/config.py` reads settings from environment variables (and a local `backend/.env` when running from `backend/`). Important values:

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | SQLite at `backend/app.db` | SQLAlchemy URL; use a PostgreSQL URL for a separately configured deployment. |
| `SECRET_KEY` | `dev-secret-key-change-me` | Development-only. Set a private strong value outside local development. |
| `ALLOWED_EMAIL_DOMAINS` | `iitm.ac.in,study.iitm.ac.in` | Comma-separated exact domains. |
| `FRONTEND_URL` | `http://localhost:5173` | Single configured CORS origin. |

Use Alembic to apply schema changes: `python -m alembic upgrade head` from `backend/`. The startup hook calls `create_all` for missing tables; it **does not** apply migrations to an existing database. No demo accounts or seed data are provided.

Public registration only allows student and mentor roles. Create a local administrator out-of-band from `backend/` with `$env:PYTHONPATH='.'; .\.venv\Scripts\python.exe create_admin.py`; the script prompts for an allowed institute email and password without echoing the password.

Request expiry is evaluated when relevant request lists, decisions, or new requests are processed; no background scheduler is configured. Suspending an account prevents protected actions and pauses active relationships. Reactivation resumes a paused relationship only if its other participant is not suspended. These policies preserve records.

## API

- Interactive OpenAPI UI: `http://localhost:8000/docs`
- Generated specification: [docs/api/openapi.yaml](docs/api/openapi.yaml)
- Endpoint overview and lifecycle notes: [docs/api/README.md](docs/api/README.md)
- Matching weights: [docs/architecture/matching.md](docs/architecture/matching.md)

Protected endpoints require `Authorization: Bearer <access_token>`. Private messages and session notes are exposed only through participant-scoped endpoints; there is no ordinary administrator read endpoint for them.

## Validation commands

```powershell
Push-Location backend
$env:PYTHONPATH = "."
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m alembic upgrade head
Pop-Location

Push-Location frontend
npm run build
npm run lint
Pop-Location
```

## Repository map

- `backend/app/api/v1/endpoints/` — authentication, profiles, matching, administration, and lifecycle APIs.
- `backend/app/models/` — SQLAlchemy entities.
- `backend/app/services/` — matching and lifecycle helpers.
- `backend/alembic/` — database migrations.
- `backend/tests/` — backend regression and lifecycle tests.
- `frontend/src/` — React application and styling.
- `docs/` — API and architecture references plus milestone planning/submission materials.

## Known limitations

- Seven-day expiry is lazy, not scheduled at the exact expiry instant.
- Capacity locking is implemented with SQL row locks; SQLite ignores `FOR UPDATE`, so production concurrency behavior must be validated on the target PostgreSQL deployment.
- The frontend is a functional starter workspace but does not yet provide every requested journey, complete field coverage, analytics filters, or comprehensive error/loading UX.
- No React test runner, automated browser suite, or genuine submission screenshot set has been verified yet.
- The development JWT secret must never be used in a deployed environment.

## Team

Team 100 — IITM BS Software Engineering project. Add verified member names and responsibilities before submission.
