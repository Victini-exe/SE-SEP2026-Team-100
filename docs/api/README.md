# API reference

The service is versioned under `/api/v1`. The machine-generated [OpenAPI document](./openapi.yaml) is the authoritative route/schema inventory; `/docs` on a running API serves the same FastAPI schema.

Regenerate the YAML after API changes from the repository root with `$env:PYTHONPATH='backend'; backend\.venv\Scripts\python.exe backend\export_openapi.py` on Windows. The export adds `x-user-stories` annotations only where this prompt supplied an explicit story mapping.

## Authentication

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/login-form`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout` (placeholder; bearer tokens are not revoked server-side)

Protected calls use `Authorization: Bearer <JWT>`. Suspended users cannot authenticate or access protected endpoints.

## Profiles, discovery, and applications

- `/api/v1/students/me/profile` — GET/PUT student profile.
- `/api/v1/students/questions` — GET/POST career questions.
- `/api/v1/mentors/apply` — submit mentor application.
- `/api/v1/mentors/me/profile` — GET/PUT mentor profile.
- `GET /api/v1/mentors/search` — paginated approved, available mentor search. Filters: query, domain, guidance type, industry, graduation year, language, experience level.
- `GET /api/v1/mentors/{mentor_id}` — public profile (no email/phone).
- `GET /api/v1/matching/recommendations` — up to five explainable matches.
- `/api/v1/admin/applications` and `/api/v1/admin/applications/{application_id}/review` — admin-only application review.

## Mentoring lifecycle

| Method and path | Access | Behavior |
|---|---|---|
| `POST /api/v1/requests` | Student | Create 100–1,000 character request to an available approved mentor; max three pending requests |
| `GET /api/v1/requests` | Student or mentor | List own requests; mentor view includes only relevant student profile and question context |
| `POST /api/v1/requests/{request_id}/decision` | Request's mentor | Accept or decline; accepts enforce capacity and create a relationship |
| `POST /api/v1/requests/{request_id}/withdraw` | Request's student | Withdraw a pending request |
| `GET /api/v1/relationships` | Participant | List own relationships and relevant mentoring context |
| `POST /api/v1/relationships/{relationship_id}/close` | Participant | Close an active relationship with a reason |
| `POST /api/v1/relationships/{relationship_id}/sessions` | Active participant | Propose an external session; local time is converted to UTC |
| `GET /api/v1/relationships/{relationship_id}/sessions` | Participant | List session history |
| `POST /api/v1/sessions/{session_id}/decision` | Participant | Confirm, mark unavailable, cancel own proposal, or complete a past confirmed session |
| `GET/POST /api/v1/relationships/{relationship_id}/messages` | Active participant for writes; participant for reads | Read/write conversation (2,000 character maximum); closed relationships are read-only |
| `GET/POST /api/v1/sessions/{session_id}/notes` | Participant | Read/write private notes and action items; late notes are flagged |
| `POST /api/v1/reports` | Student or mentor | Submit report on another user |
| `GET /api/v1/notifications` and `POST /api/v1/notifications/{notification_id}/read` | Owner | List and mark own persistent notifications |

Requests expire after seven days when a request list, decision, or creation operation runs the lazy expiry sweep. There is no background scheduler in this repository.

## Administration

- `GET /api/v1/admin/dashboard`, `/users`, `/applications`
- `GET /api/v1/admin/reports` and `POST /api/v1/admin/reports/{report_id}/review`
- `POST /api/v1/admin/users/{user_id}/suspend`
- `POST /api/v1/admin/users/{user_id}/reactivate`
- `GET /api/v1/admin/alerts`
- `GET /api/v1/admin/analytics?start=<ISO-8601>&end=<ISO-8601>`

Admin analytics are aggregate-only; small career-goal/interest groups are suppressed. Admin routes do not expose message bodies or private session notes.

## Error behavior

- `401`: missing/invalid token or suspended account during login.
- `403`: authenticated role is not permitted.
- `404`: object missing or not visible to the caller.
- `409`: lifecycle conflict, capacity/availability conflict, duplicate pending request, or invalid transition.
- `422`: request/schema validation, including field lengths and timezone errors.

The precise request/response schemas and generated security requirements are in `openapi.yaml`. User-story annotations are supplied as `x-user-stories` extensions where mapped.
