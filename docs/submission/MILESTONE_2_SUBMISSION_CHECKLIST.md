# Milestone 2 submission checklist

Milestone 2 is described as “Scheduling and Design”; the project plan separately identifies Sprint 1 as API Development and Sprint 2 as Testing, Integration and User Feedback. This checklist reports repository evidence, not a claim that every definition of done is complete.

| Deliverable | Repository location | Status |
|---|---|---|
| Main setup and project README | [`README.md`](../../README.md) | Updated; lists current scope and known gaps |
| API description | [`docs/api/README.md`](../api/README.md) | In progress with implemented endpoints |
| OpenAPI YAML | [`docs/api/openapi.yaml`](../api/openapi.yaml) | Generated from the running FastAPI app; validate again after endpoint changes |
| Component design | [`docs/architecture/component-design.md`](../architecture/component-design.md) | Created from the current modular monolith |
| Architecture overview | [`docs/architecture/README.md`](../architecture/README.md) | Update/verify alongside implementation |
| Class diagram | [`docs/diagrams/class-diagram.mmd`](../diagrams/class-diagram.mmd) | Created; verify after future model changes |
| Database ER diagram | [`docs/diagrams/database-er-diagram.mmd`](../diagrams/database-er-diagram.mmd) | Created; verify against migrations |
| Sprint schedule | [`docs/project-management/sprint-schedule.md`](../project-management/sprint-schedule.md) | Relative schedule; no calendar dates or names invented |
| Scrum cadence/minutes template | [`docs/project-management/scrum-meetings.md`](../project-management/scrum-meetings.md) | Proposed cadence/template only; no fabricated meeting minutes |
| Gantt chart | [`docs/project-management/gantt-chart.mmd`](../project-management/gantt-chart.mmd) | Editable relative schedule; placeholder dates must be shifted to match team plan |
| Kanban board | [`docs/project-management/kanban-board.md`](../project-management/kanban-board.md) | Local board; remote project not created |
| Genuine application screenshots | `docs/submission/screenshots/` | Not complete; only capture pages that are running and represent real implementation |
| Frontend release ZIP | `frontend-release.zip` | Generated from the frontend source; inspected to include package files/README and exclude `node_modules`/build output |
| Backend tests | `backend/tests/` | Run locally; see final verification results |
| Frontend unit/E2E tests | `frontend/` | Not configured |
| Git branch/commits/PR | Current feature branch | Verify final commits, push, and PR separately; do not claim remote publication before confirmation |

## Known gaps before calling the milestone complete

- Full student, mentor, and administrator journeys and all T100/US acceptance criteria are not implemented end to end.
- Frontend automated tests and full browser coverage are absent.
- PostgreSQL concurrency, realistic search performance, production deployment, and user feedback remain unverified.
- No remote GitHub Project, screenshots set, or release archive should be represented as done until created and inspected.
