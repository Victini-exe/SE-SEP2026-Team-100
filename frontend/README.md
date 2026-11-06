# IITM BS Mentoring Platform frontend

The frontend is a React + TypeScript application built with Vite and React Router. It currently provides registration/login and starter student, mentor, and administrator workspaces backed by the FastAPI API.

## Requirements

- Node.js 22+
- npm
- The FastAPI backend running at `http://localhost:8000`

## Install and run

```powershell
npm ci
npm run dev -- --host localhost --port 5173
```

Set `VITE_API_BASE_URL` when the backend is hosted at a different origin, for example:

```powershell
$env:VITE_API_BASE_URL = "http://localhost:8000/api/v1"
npm run dev -- --host localhost --port 5173
```

The backend must allow the frontend origin through its `FRONTEND_URL` setting.

## Validation

```powershell
npm run build
npm run lint
```

There is not yet a frontend unit-test runner or automated browser test suite.
