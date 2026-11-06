# API documentation

The platform exposes its backend through the `/api/v1` prefix.

## Authentication endpoints

- `POST /api/v1/auth/register` – create a user with a valid institute email
- `POST /api/v1/auth/login` – login and receive a bearer token
- `POST /api/v1/auth/login-form` – OAuth2 form login endpoint
- `GET /api/v1/auth/me` – fetch current user profile
- `POST /api/v1/auth/logout` – logout placeholder endpoint

## Student endpoints

- `GET /api/v1/students/me/profile` – fetch the signed-in student profile
- `PUT /api/v1/students/me/profile` – update the student profile
- `GET /api/v1/students/questions` – list the student’s career questions
- `POST /api/v1/students/questions` – create a new career question

## Mentor endpoints

- `POST /api/v1/mentors/apply` – submit mentor application
- `GET /api/v1/mentors/me/profile` – fetch current mentor profile
- `PUT /api/v1/mentors/me/profile` – update mentor profile
- `GET /api/v1/mentors/search` – search approved mentors
- `GET /api/v1/mentors/{mentor_id}` – fetch public mentor information

## Matching endpoints

- `GET /api/v1/matching/recommendations` – personalized mentor recommendations for students

## Admin endpoints

- `GET /api/v1/admin/dashboard` – fetch admin summary metrics
- `GET /api/v1/admin/applications` – list all mentor applications
- `POST /api/v1/admin/applications/{application_id}/review` – approve or reject mentor applications

## Notes

The generated OpenAPI schema is available from the FastAPI app at `/docs` when the backend is running.
