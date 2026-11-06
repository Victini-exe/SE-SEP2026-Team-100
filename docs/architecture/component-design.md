# Component design

## Runtime shape

The project is a modular monolith. The React SPA calls one versioned FastAPI service, which validates access and writes to one relational database. There is no separate service process, queue, email provider, or video-call service.

```text
Browser
  React + TypeScript + React Router
  ├─ Auth form and bearer-token storage
  ├─ Student workspace
  ├─ Mentor workspace
  └─ Admin workspace
          │ JSON / Authorization: Bearer
          ▼
FastAPI /api/v1
  ├─ auth endpoints ───────── JWT/password helpers
  ├─ students endpoints ───── profiles and career questions
  ├─ mentors endpoints ────── applications, profiles, search
  ├─ matching endpoint ────── explainable scoring service
  ├─ lifecycle endpoints ──── requests, relationships, sessions,
  │                            messages, notes, reports, notifications
  └─ admin endpoints ──────── application decisions and user listing
          │ SQLAlchemy ORM / Alembic
          ▼
SQLite (local) / relational database (configured deployment)
```

## Frontend modules

- `src/main.tsx` mounts the app under `BrowserRouter`.
- `src/App.tsx` owns login/registration, authenticated identity lookup, role-aware workspace selection, API requests, and page-level state.
- `src/App.css` and `src/index.css` provide the shared responsive visual styles.
- API calls use `VITE_API_BASE_URL` when set, otherwise `http://localhost:8000/api/v1`.
- The current token is stored in browser `localStorage`; a production deployment should review token storage and add a stronger session/refresh strategy.

The UI is a starter operational workflow, not a complete implementation of every requested screen. No shared query cache, component library, form-validation package, or frontend automated test framework is installed.

## Backend boundaries

- `app/api/v1/endpoints/` is the HTTP and authorization boundary.
- `app/schemas/` validates request shapes and limits.
- `app/services/matching.py` computes match scores and explanations.
- `app/services/lifecycle.py` centralizes UTC helpers, persistent notifications, and lazy request expiration.
- `app/models/` defines entities, foreign keys, uniqueness, indexes, and status constraints.
- `app/db/session.py` owns the SQLAlchemy engine/session and creates missing tables at startup.
- `alembic/` holds forward and reverse schema migrations. Startup `create_all` is not a substitute for applying migrations to an existing database.

## Data flows and controls

1. Registration hashes passwords and creates role-scoped users. Mentor registration remains pending verification until an administrator approves the application.
2. Protected routes resolve the JWT subject to a database user; suspended users are rejected before business operations.
3. Students submit requests only for approved, active, available mentors. A partial unique index prevents concurrent duplicate pending requests.
4. Acceptance locks the mentor profile where supported, checks capacity again, transitions the request and creates a relationship in one transaction.
5. Session timestamps are normalized to UTC using the supplied IANA timezone; ambiguous/nonexistent naive local times are rejected.
6. Message, session, and note reads are scoped to a relationship participant. No ordinary admin endpoint reads message bodies or private notes.
7. Admin account actions add audit rows. Suspension blocks access and pauses active relationships; reactivation resumes them only if the other party is no longer suspended.
8. Analytics return aggregate counts. Career goals and interests with fewer than three records are omitted to reduce small-group disclosure.

## Transaction and operational notes

- PostgreSQL row locks serialize mentor acceptance and student pending-request counts. SQLite does not implement `SELECT ... FOR UPDATE`, so production concurrency must be verified on PostgreSQL.
- Request expiry is a lazy sweep on request listing, creation, and mentor decisions; no scheduler is configured.
- Messages are not written to application logs. Notifications contain generic event text, not message content.
- There is no repository layer separate from SQLAlchemy sessions; endpoints currently query the ORM directly. Extracting repositories is not warranted until the codebase grows further.
