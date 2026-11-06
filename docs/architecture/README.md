# Architecture overview

## System goals

The mentoring platform is designed as a modular monolith so that the core domain remains easy to extend while still keeping deployment and operations straightforward for a student-facing platform.

## Core components

### Frontend

The frontend is a React + TypeScript single-page application served by Vite. It exposes the main screens for landing, login, registration, and role-based user experiences.

### Backend

The backend is a FastAPI application built around a modular routing structure. The `api/v1` router groups auth, student, mentor, admin, and matching flows into a single operational API surface.

### Data layer

The application uses SQLAlchemy models with SQLite by default for local development. Entity relationships model users, profiles, specialty interests, mentoring requests, and notification data.

### Matching engine

Mentor recommendations are calculated using a scoring function that considers:
- career goal alignment
- interest overlap
- language preference
- experience level
- mentor capacity and status

## Deployment assumptions

The platform is designed for a simple local stack first, with a clear path to future production upgrades:
- move from SQLite to PostgreSQL
- add background task queues and notifications
- add richer admin review and session workflows
- expose deployment through Docker or cloud infrastructure

## Key architectural decisions

- Use a single codebase to keep domain logic and data contracts cohesive
- Keep route modules grouped by persona and business capability
- Centralize JWT and password logic in `auth` utilities
- Keep profile and mentoring logic in dedicated service and schema layers
