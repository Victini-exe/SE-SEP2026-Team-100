# Architecture overview

The platform is a single deployable React SPA and FastAPI modular monolith backed by SQLAlchemy and a relational database. SQLite is the local default; database schema evolution is managed by Alembic.

See [component-design.md](./component-design.md) for runtime modules and trust boundaries, [class-diagram.mmd](../diagrams/class-diagram.mmd) for domain relationships, and [database-er-diagram.mmd](../diagrams/database-er-diagram.mmd) for the relational schema.

## Important decisions and limits

- Role and record authorization are enforced in the API, not only in the UI.
- Request acceptance rechecks mentor capacity and uses row locks where the database supports them. SQLite does not provide equivalent `FOR UPDATE` concurrency guarantees.
- Session instants are stored in UTC. IANA timezone data is included for Windows/local runtime conversions.
- Admin actions create audit rows. Normal admin APIs do not expose private message content or session notes.
- Account suspension pauses active relationships without deleting history. Reactivation resumes a relationship only when the other participant is not suspended.
- Seven-day request expiration is lazy and occurs when relevant lifecycle routes are used; a scheduled worker is not configured.
- The default development JWT secret is unsafe for deployment. Configure a private secret and deployment settings before hosting.
