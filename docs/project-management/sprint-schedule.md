# Milestone and sprint schedule

This is an editable relative schedule. No calendar dates, team-member names, or completed meetings were supplied, so none are asserted here. Replace `Week N` and owner placeholders with the team's agreed schedule.

## Milestone 2 — Scheduling and Design

| Relative window | Goal | Tasks | Deliverables | Owner | Dependencies / acceptance |
|---|---|---|---|---|---|
| Week 1 | Agree scope and design | Verify merged foundation; refine role journeys, lifecycle states, data model, privacy policy, API contracts, and acceptance criteria | Approved schedule/design package; diagrams; prioritized backlog | Developer A / Developer B (confirm) | Foundation is present on main; review business rules and privacy with team |

Milestone 2 is the project milestone label (“Scheduling and Design”); the implementation work below is split into the two project sprints.

## Sprint 1 — API Development

| Relative window | Goal | Tasks | Deliverables | Owner | Dependencies / acceptance |
|---|---|---|---|---|---|
| Weeks 2–3 | Implement and connect the core platform workflows | Request lifecycle; role authorization; relationship closure; session/messaging/note APIs; reports/moderation; migrations; React API integration | Migrated relational schema; working API routes; integrated role workspaces | Developer B (proposed), Developer A (review) | Design decisions accepted; all business rules server-side; participant access tests pass |

## Sprint 2 — Testing, Integration and User Feedback

| Relative window | Goal | Tasks | Deliverables | Owner | Dependencies / acceptance |
|---|---|---|---|---|---|
| Weeks 4–5 | Validate integration and prepare submission | Complete missing role journeys; browser tests; PostgreSQL concurrency validation; accessibility and responsive review; collect and record actual user feedback; finish documentation and evidence | Reproducible test results; verified screenshots; release ZIP; submission checklist | Developer A / Developer B (confirm) | Sprint 1 APIs integrated; feedback collected before being reported; no mock workflows presented as complete |

## Acceptance criteria

- Every card marked Done on the [Kanban board](./kanban-board.md) has implementation evidence and a passing focused test or command.
- Do not promote incomplete UI coverage, PostgreSQL concurrency, user feedback, or screenshots to Done without actual verification.
- Record real calendar dates, owners, and user feedback only after the team supplies them.
