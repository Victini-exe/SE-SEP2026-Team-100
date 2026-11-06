# IITM BS Student Mentoring Platform

A modular monolith implementation for an IITM BS mentoring platform that connects students, mentors, and administrators.

## Overview

This project supports:
- Student onboarding and profile management
- Mentor applications and profile verification
- Matching recommendations based on career goals, interests, and availability
- Admin review workflows for mentor applications
- JWT-based authentication with institute email validation
- A Vite + React frontend and FastAPI backend

## Stack

- Frontend: React, TypeScript, Vite, React Router
- Backend: FastAPI, SQLAlchemy, Pydantic, JWT
- Database: SQLite for local development
- Testing: pytest

## Repository structure

- `backend/` – FastAPI application, schemas, models, services, and tests
- `frontend/` – React application shell and UI pages
- `docs/` – API, architecture, and handover documentation
- `scripts/` – operational utilities

## Local development

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. pytest -q
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

## API base URL

- Backend: `http://localhost:8000/api/v1`
- Frontend: `http://localhost:5173`

## Authentication behavior

- Users must register with an IITM email address domain
- Roles supported: `student`, `mentor`, and `admin`
- Access tokens are issued through JWT
- Mentor accounts are put into a pending verification state until reviewed by an admin

## Current status

The project includes a working foundation with backend auth tests passing and a polished frontend shell. The next steps are to expand operational workflows, add more user journeys, and complete the full project documentation set.