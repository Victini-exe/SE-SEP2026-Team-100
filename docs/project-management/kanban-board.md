# Local Kanban board

This repository board reflects the implementation state observed during this change. It is not a live GitHub Project. Do not copy cards into Done without rerunning their acceptance checks.

## Backlog

| Card | Scope | Acceptance |
|---|---|---|
| T100-20/21 | Complete student accepted-mentor and mentor assigned-mentee detail views | UI includes relationship metadata, profile context, last activity, and useful actions |
| T100-24/25/26 | Finish session, messaging, and notes UX | Reschedule and cancellation flows, note action-item entry, loading/error/empty states, and accessibility covered |
| T100-27/28 | Complete report-management and account action UX | Category selection, review-note input, reason confirmation, audit evidence |
| US-01–US-20, US-23–US-24 | Reconcile against the official Milestone 1 story text | Exact story acceptance criteria mapped; the source story descriptions were not included in the supplied prompt |
| Performance | Test realistic mentor search/recommendations dataset | Measured query time and dataset recorded; do not promise a 2-second threshold before measurement |
| Production readiness | PostgreSQL, secure secrets, backups, retention, and deployment policy | Deployment configuration and security review approved |

## To Do

| Card | Scope |
|---|---|
| Frontend tests | Add a maintained test runner and tests for validation, auth state, and role workspaces |
| End-to-end | Automate student-to-mentor lifecycle in a disposable database |
| PostgreSQL concurrency | Verify capacity and duplicate-request races against PostgreSQL |
| Domain analytics | Review privacy thresholds and implement the requested shortage/category reporting UX |
| Submission evidence | Capture real screens for routes that are actually implemented and verified |

## In Progress

| Card | Scope |
|---|---|
| T100-18–19, 22–23 | Backend request lifecycle, limit, withdrawal, acceptance, expiry sweep, and closure |
| T100-24–26 | Backend sessions, timezone conversion, messages, and notes |
| T100-27–28 / US-21–22 | Backend report review, suspension, aggregate metrics, and inactivity alerts |
| Role workspaces | Connect starter React views to implemented endpoints; UI coverage remains partial |
| Integration and documentation | Validate migration/OpenAPI and accurately record gaps |

## Review

| Card | Evidence required |
|---|---|
| Lifecycle backend | `pytest` results, migration upgrade/downgrade, authorization and business-rule tests |
| Frontend integration | Production build, ESLint, browser registration/login check, manual role-by-role review |
| Documentation package | Verify generated OpenAPI against runtime routes; review all design diagrams against ORM models |

## Done

| Card | Evidence |
|---|---|
| Developer A foundation merged | `origin/main` history includes foundation commit `4de7ed9` and merge commit `85f5eb5` |
| Python environment for local validation | Python 3.13 venv with pinned backend dependencies and Windows timezone data |

## GitHub Projects recreation

Create a board for `Victini-exe/SE-SEP2026-Team-100` with columns Backlog, To Do, In Progress, Review, Done. Copy each card above, add the listed acceptance criteria as the issue body, and link implementation PRs. No remote project was created by this change.
