# Milestone 3 - API test cases

Generated from a real pytest run on 2026-11-17 17:08:12 UTC. Inputs, expected output and actual output are recorded by the test suite itself.

| | Count |
|---|---|
| Test cases | 284 |
| Success | 275 |
| Fail | 9 |
| Endpoints exercised (method + route) | 42 |

Endpoints covered: `GET /api/v1/admin/alerts`, `GET /api/v1/admin/analytics`, `GET /api/v1/admin/applications`, `GET /api/v1/admin/dashboard`, `GET /api/v1/admin/reports`, `GET /api/v1/admin/users`, `GET /api/v1/auth/me`, `GET /api/v1/matching/recommendations`, `GET /api/v1/mentors/me/profile`, `GET /api/v1/mentors/search`, `GET /api/v1/mentors/{id}`, `GET /api/v1/notifications`, `GET /api/v1/relationships`, `GET /api/v1/relationships/{id}/messages`, `GET /api/v1/relationships/{id}/sessions`, `GET /api/v1/requests`, `GET /api/v1/sessions/{id}/notes`, `GET /api/v1/students/me/profile`, `GET /api/v1/students/questions`, `GET /health`, `POST /api/v1/admin/applications/{id}/review`, `POST /api/v1/admin/reports/{id}/review`, `POST /api/v1/admin/users/{id}/reactivate`, `POST /api/v1/admin/users/{id}/suspend`, `POST /api/v1/auth/login`, `POST /api/v1/auth/login-form`, `POST /api/v1/auth/logout`, `POST /api/v1/auth/register`, `POST /api/v1/mentors/apply`, `POST /api/v1/notifications/{id}/read`, `POST /api/v1/relationships/{id}/close`, `POST /api/v1/relationships/{id}/messages`, `POST /api/v1/relationships/{id}/sessions`, `POST /api/v1/reports`, `POST /api/v1/requests`, `POST /api/v1/requests/{id}/decision`, `POST /api/v1/requests/{id}/withdraw`, `POST /api/v1/sessions/{id}/decision`, `POST /api/v1/sessions/{id}/notes`, `POST /api/v1/students/questions`, `PUT /api/v1/mentors/me/profile`, `PUT /api/v1/students/me/profile`

## Defects found by testing (actual output differs from expected)

| Test case | API | Defect |
|---|---|---|
| TC-036 After logout the old token should no longer work | `GET /api/v1/auth/me` | Logout does not revoke the token: the old token still works afterwards (JWT is stateless and there is no deny-list). |
| TC-052 Each profile change is kept with its date | `PUT /api/v1/students/me/profile` | US-06 asks for each profile change to be saved with a date; profile_history is never written and no change log exists. |
| TC-069 An application without roll number, graduation year or LinkedIn should be rejected | `POST /api/v1/mentors/apply` | US-02 requires roll number, graduation year and LinkedIn URL, but all three are optional: an empty application is accepted. |
| TC-082 An unknown pause status should be rejected with 422 | `PUT /api/v1/mentors/me/profile` | pause_status is not validated by the schema; an unknown value hits the database CHECK constraint and returns 500 instead of 422. |
| TC-083 An unknown experience level should be rejected with 422 | `PUT /api/v1/mentors/me/profile` | experience_level is not validated by the schema; an unknown value hits the database CHECK constraint and returns 500 instead of 422. |
| TC-103 Mentor search should require a logged-in user | `GET /api/v1/mentors/search` | Mentor search is public: it works without logging in, although US-01 limits the platform to verified students. |
| TC-108 A suspended mentor's public profile should no longer be shown | `GET /api/v1/mentors/1` | The public profile only checks the profile is approved, not that the user is active, so a suspended mentor's profile stays visible. |
| TC-122 An application that was already approved cannot be reviewed again | `POST /api/v1/admin/applications/1/review` | A decided application can be reviewed again. Rejecting after approval marks it rejected but leaves the mentor profile approved and searchable. |
| TC-140 A student sends a request to a mentor straight from the recommendations | `POST /api/v1/requests` | Recommendations return mentor_id = mentor PROFILE id, but POST /requests expects the mentor USER id, so requesting a recommended mentor fails (404). |

## How to run

```bash
cd backend
python -m pytest -v -rxX
```

## Authentication and health

Source: `backend/tests/test_api_auth.py`

### TC-001: A student registers with an IITM BS institute email

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/register`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"name": "Asha Raman", "institute_email": "student-b6b5da5a80@study.iitm.ac.in", "password": "password123", "role": "student"}`

**Expected Output:**
- HTTP Status Code: 201
- JSON containing: `{"name": "Asha Raman", "institute_email": "student-b6b5da5a80@study.iitm.ac.in", "role": "student", "account_status": "active"}`

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 1, "name": "Asha Raman", "institute_email": "student-b6b5da5a80@study.iitm.ac.in", "role": "student", "account_status": "active"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_register_student_with_institute_email`

---

### TC-002: A mentor registration waits for admin verification

**User stories:** US-02, US-03

**API being tested:** `POST /api/v1/auth/register`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"name": "Ravi Kumar", "institute_email": "mentor-1a538c72c1@study.iitm.ac.in", "password": "password123", "role": "mentor"}`

**Expected Output:**
- HTTP Status Code: 201
- JSON containing: `{"role": "mentor", "account_status": "pending_verification"}`

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 1, "name": "Ravi Kumar", "institute_email": "mentor-1a538c72c1@study.iitm.ac.in", "role": "mentor", "account_status": "pending_verification"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_register_mentor_starts_pending_verification`

---

### TC-003: Registration accepts the other configured domain, iitm.ac.in

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/register`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"name": "Staff Student", "institute_email": "someone.new@iitm.ac.in", "password": "password123", "role": "student"}`

**Expected Output:**
- HTTP Status Code: 201
- JSON containing: `{"institute_email": "someone.new@iitm.ac.in"}`

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 1, "name": "Staff Student", "institute_email": "someone.new@iitm.ac.in", "role": "student", "account_status": "active"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_register_accepts_second_allowed_domain`

---

### TC-004: Registration stores the email in lower case

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/register`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"name": "Mixed Case", "institute_email": "Mixed.Case@Study.IITM.ac.in", "password": "password123", "role": "student"}`

**Expected Output:**
- HTTP Status Code: 201
- JSON containing: `{"institute_email": "mixed.case@study.iitm.ac.in"}`

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 1, "name": "Mixed Case", "institute_email": "mixed.case@study.iitm.ac.in", "role": "student", "account_status": "active"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_register_stores_email_in_lower_case`

---

### TC-005: Registration with a Gmail address is rejected

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/register`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"name": "Outsider", "institute_email": "outsider@gmail.com", "password": "password123", "role": "student"}`

**Expected Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "Institute email domain not allowed"}`

**Actual Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "Institute email domain not allowed"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_register_rejects_non_institute_email`

---

### TC-006: Registration with a look-alike domain (fakestudy.iitm.ac.in) is rejected

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/register`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"name": "Spoofer", "institute_email": "x@fakestudy.iitm.ac.in", "password": "password123", "role": "student"}`

**Expected Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "Institute email domain not allowed"}`

**Actual Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "Institute email domain not allowed"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_register_rejects_lookalike_domain`

---

### TC-007: Registering the same email twice is rejected

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/register`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"name": "First User", "institute_email": "dup-cbdd538328@study.iitm.ac.in", "password": "password123", "role": "student"}`

**Expected Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "User already exists"}`

**Actual Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "User already exists"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_register_rejects_duplicate_email`

---

### TC-008: An email that differs only in letter case counts as a duplicate

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/register`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"name": "Upper", "institute_email": "CASE-3408D42E8D@STUDY.IITM.AC.IN", "password": "password123", "role": "student"}`

**Expected Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "User already exists"}`

**Actual Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "User already exists"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_register_rejects_duplicate_email_with_different_case`

---

### TC-009: Public registration cannot create an administrator

**User stories:** US-03

**API being tested:** `POST /api/v1/auth/register`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"name": "Not Admin", "institute_email": "adm-d07198ef16@study.iitm.ac.in", "password": "password123", "role": "admin"}`

**Expected Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "Only student and mentor registration is available"}`

**Actual Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "Only student and mentor registration is available"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_register_cannot_create_admin`

---

### TC-010: Role 'MENTOR' in capitals is accepted and stored as 'mentor'

**User stories:** US-02

**API being tested:** `POST /api/v1/auth/register`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"name": "Caps Mentor", "institute_email": "caps-726f3930d5@study.iitm.ac.in", "password": "password123", "role": "MENTOR"}`

**Expected Output:**
- HTTP Status Code: 201
- JSON containing: `{"role": "mentor"}`

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 1, "name": "Caps Mentor", "institute_email": "caps-726f3930d5@study.iitm.ac.in", "role": "mentor", "account_status": "pending_verification"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_register_role_is_case_insensitive`

---

### TC-011: Registration rejects out-of-range fields with 422 [password-7-chars]

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/register`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"name": "Valid Name", "institute_email": "val-eaa83a2873@study.iitm.ac.in", "password": "short7!", "role": "student"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_short", "loc": ["body", "password"], "msg": "String should have at least 8 characters", "input": "short7!", "ctx": {"min_length": 8}}]}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_register_validates_fields[password-7-chars]`

---

### TC-012: Registration rejects out-of-range fields with 422 [password-129-chars]

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/register`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"name": "Valid Name", "institute_email": "val-56ab13939b@study.iitm.ac.in", "password": "<129 characters: 'xxxxxxxxxxxx'...>", "role": "student"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_long", "loc": ["body", "password"], "msg": "String should have at most 128 characters", "input": "<129 characters: 'xxxxxxxxxxxx'...>", "ctx": {"max_length": 128}}]}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_register_validates_fields[password-129-chars]`

---

### TC-013: Registration rejects out-of-range fields with 422 [name-1-char]

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/register`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"name": "A", "institute_email": "val-be64a41ccf@study.iitm.ac.in", "password": "password123", "role": "student"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_short", "loc": ["body", "name"], "msg": "String should have at least 2 characters", "input": "A", "ctx": {"min_length": 2}}]}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_register_validates_fields[name-1-char]`

---

### TC-014: Registration rejects out-of-range fields with 422 [name-151-chars]

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/register`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"name": "<151 characters: 'NNNNNNNNNNNN'...>", "institute_email": "val-83f422b814@study.iitm.ac.in", "password": "password123", "role": "student"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_long", "loc": ["body", "name"], "msg": "String should have at most 150 characters", "input": "<151 characters: 'NNNNNNNNNNNN'...>", "ctx": {"max_length": 150}}]}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_register_validates_fields[name-151-chars]`

---

### TC-015: Registration rejects out-of-range fields with 422 [malformed-email]

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/register`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"name": "Valid Name", "institute_email": "not-an-email", "password": "password123", "role": "student"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "value_error", "loc": ["body", "institute_email"], "msg": "value is not a valid email address: An email address must have an @-sign.", "input": "not-an-email", "ctx": {"reason": "An email address must have an @-sign."}}]}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_register_validates_fields[malformed-email]`

---

### TC-016: Registration without an email is rejected with 422

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/register`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"name": "No Email", "password": "password123"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "missing", "loc": ["body", "institute_email"], "msg": "Field required", "input": {"name": "No Email", "password": "password123"}}]}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_register_requires_email`

---

### TC-017: A registered student logs in and receives a bearer token

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/login`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"institute_email": "student-32c948cf33@study.iitm.ac.in", "password": "password123"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"token_type": "bearer"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"access_token": "<JWT access token>", "token_type": "bearer"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_login_returns_bearer_token`

---

### TC-018: The login token expires within 24 hours

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/login`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"institute_email": "student-2f3392c140@study.iitm.ac.in", "password": "password123"}`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"access_token": "<JWT access token>", "token_type": "bearer"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_login_token_lasts_at_most_24_hours`

---

### TC-019: Login works with the email typed in capitals

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/login`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"institute_email": "STUDENT-C79AD759A9@STUDY.IITM.AC.IN", "password": "password123"}`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"access_token": "<JWT access token>", "token_type": "bearer"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_login_email_is_case_insensitive`

---

### TC-020: A successful login records the last login time

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/login`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"institute_email": "student-eaec88d9a9@study.iitm.ac.in", "password": "password123"}`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"access_token": "<JWT access token>", "token_type": "bearer"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_login_records_last_login_time`

---

### TC-021: Login with a wrong password is rejected

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/login`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"institute_email": "student-e0e105c668@study.iitm.ac.in", "password": "wrong-password"}`

**Expected Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Invalid credentials"}`

**Actual Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Invalid credentials"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_login_rejects_wrong_password`

---

### TC-022: Login with an email that is not registered is rejected

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/login`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"institute_email": "nobody@study.iitm.ac.in", "password": "password123"}`

**Expected Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Invalid credentials"}`

**Actual Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Invalid credentials"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_login_rejects_unknown_email`

---

### TC-023: A suspended user cannot log in

**User stories:** US-24

**API being tested:** `POST /api/v1/auth/login`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"institute_email": "student-2dc44e2b72@study.iitm.ac.in", "password": "password123"}`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Account suspended"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Account suspended"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_login_blocks_suspended_account`

---

### TC-024: Login without a password field is rejected with 422

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/login`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"institute_email": "a@study.iitm.ac.in"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "missing", "loc": ["body", "password"], "msg": "Field required", "input": {"institute_email": "a@study.iitm.ac.in"}}]}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_login_requires_password_field`

---

### TC-025: The OAuth2 form login (used by Swagger 'Authorize') returns a token

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/login-form`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- Form data: `{"username": "student-c9e5d8b39d@study.iitm.ac.in", "password": "<password>"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"token_type": "bearer"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"access_token": "<JWT access token>", "token_type": "bearer"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_login_form_returns_token`

---

### TC-026: The form login rejects a wrong password

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/login-form`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- Form data: `{"username": "student-dfde85aa8f@study.iitm.ac.in", "password": "<password>"}`

**Expected Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Invalid credentials"}`

**Actual Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Invalid credentials"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_login_form_rejects_wrong_password`

---

### TC-027: The form login without a username is rejected with 422

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/login-form`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- Form data: `{"password": "<password>"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "missing", "loc": ["body", "username"], "msg": "Field required", "input": null}]}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_login_form_requires_username`

---

### TC-028: /auth/me returns the logged-in user

**User stories:** US-01

**API being tested:** `GET /api/v1/auth/me`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "name": "Meera Iyer", "institute_email": "student-e0bb14db00@study.iitm.ac.in", "role": "student", "account_status": "active"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "name": "Meera Iyer", "institute_email": "student-e0bb14db00@study.iitm.ac.in", "role": "student", "account_status": "active"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_me_returns_current_user`

---

### TC-029: /auth/me without a token is rejected

**User stories:** US-01

**API being tested:** `GET /api/v1/auth/me`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)

**Expected Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Not authenticated"}`

**Actual Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Not authenticated"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_me_without_token`

---

### TC-030: /auth/me with a malformed token is rejected

**User stories:** US-01

**API being tested:** `GET /api/v1/auth/me`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <custom token token>`

**Expected Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Could not validate credentials"}`

**Actual Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Could not validate credentials"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_me_with_garbage_token`

---

### TC-031: /auth/me with an expired token is rejected

**User stories:** US-01

**API being tested:** `GET /api/v1/auth/me`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <custom token token>`

**Expected Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Could not validate credentials"}`

**Actual Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Could not validate credentials"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_me_with_expired_token`

---

### TC-032: /auth/me with a token signed by another key is rejected

**User stories:** US-01

**API being tested:** `GET /api/v1/auth/me`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <custom token token>`

**Expected Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Could not validate credentials"}`

**Actual Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Could not validate credentials"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_me_with_token_signed_by_wrong_key`

---

### TC-033: /auth/me with a valid token for a user that does not exist is rejected

**User stories:** US-01

**API being tested:** `GET /api/v1/auth/me`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <custom token token>`

**Expected Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Could not validate credentials"}`

**Actual Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Could not validate credentials"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_me_with_token_for_unknown_user`

---

### TC-034: An already-issued token stops working once the user is suspended

**User stories:** US-24

**API being tested:** `GET /api/v1/auth/me`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Account suspended"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Account suspended"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_me_rejects_token_of_suspended_user`

---

### TC-035: Logout returns a confirmation message

**User stories:** US-01

**API being tested:** `POST /api/v1/auth/logout`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)

**Expected Output:**
- HTTP Status Code: 200
- JSON: `{"detail": "Logged out"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"detail": "Logged out"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_logout_returns_confirmation`

---

### TC-036: After logout the old token should no longer work

**User stories:** US-01

**Step 1: API being tested:** `POST /api/v1/auth/logout`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- (no expectation recorded for this call)

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"detail": "Logged out"}`

**Step 2: API being tested:** `GET /api/v1/auth/me`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 401

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "name": "Student 1", "institute_email": "student-d14aef3458@study.iitm.ac.in", "role": "student", "account_status": "active"}`

**Result:** Fail

> **Defect found:** Logout does not revoke the token: the old token still works afterwards (JWT is stateless and there is no deny-list).

pytest: `tests/test_api_auth.py::test_logout_invalidates_token`

---

### TC-037: The health check reports the service is up

**API being tested:** `GET /health`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)

**Expected Output:**
- HTTP Status Code: 200
- JSON: `{"status": "ok"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"status": "ok"}`

**Result:** Success

pytest: `tests/test_api_auth.py::test_health_check`

---

## Student profile and career questions

Source: `backend/tests/test_api_students.py`

### TC-038: A new student has no mentoring profile yet

**User stories:** US-04

**API being tested:** `GET /api/v1/students/me/profile`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Student profile not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Student profile not found"}`

**Result:** Success

pytest: `tests/test_api_students.py::test_get_profile_before_creating_one`

---

### TC-039: A student reads back the profile they saved

**User stories:** US-04

**API being tested:** `GET /api/v1/students/me/profile`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"career_goal": "Job", "current_situation": "Final-year BS student working part-time", "preferred_language": "English", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "Data scientist in a product company", "interest_area_ids": [1], "user_id": 1}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"career_goal": "Job", "current_situation": "Final-year BS student working part-time", "preferred_language": "English", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "Data scientist in a product company", "interest_area_ids": [1], "id": 1, "user_id": 1}`

**Result:** Success

pytest: `tests/test_api_students.py::test_get_profile_returns_saved_profile`

---

### TC-040: A mentor cannot use the student profile endpoint

**User stories:** US-04

**API being tested:** `GET /api/v1/students/me/profile`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <mentor token>`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Student access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Student access required"}`

**Result:** Success

pytest: `tests/test_api_students.py::test_get_profile_forbidden_for_mentor`

---

### TC-041: The student profile cannot be read without logging in

**User stories:** US-01, US-04

**API being tested:** `GET /api/v1/students/me/profile`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)

**Expected Output:**
- HTTP Status Code: 401

**Actual Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Not authenticated"}`

**Result:** Success

pytest: `tests/test_api_students.py::test_get_profile_requires_login`

---

### TC-042: A student creates a mentoring profile with goal, interests, language and availability

**User stories:** US-04

**API being tested:** `PUT /api/v1/students/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <student token>`
- JSON: `{"career_goal": "Job", "current_situation": "Final-year BS student working part-time", "preferred_language": "English", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "Data scientist in a product company", "interest_area_ids": [1, 2]}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"career_goal": "Job", "current_situation": "Final-year BS student working part-time", "preferred_language": "English", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "Data scientist in a product company", "interest_area_ids": [1, 2]}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"career_goal": "Job", "current_situation": "Final-year BS student working part-time", "preferred_language": "English", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "Data scientist in a product company", "interest_area_ids": [1, 2], "id": 1, "user_id": 1}`

**Result:** Success

pytest: `tests/test_api_students.py::test_create_profile_with_goal_interests_language_availability`

---

### TC-043: Updating the profile replaces the old goal and interests

**User stories:** US-06

**API being tested:** `PUT /api/v1/students/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <student token>`
- JSON: `{"career_goal": "Entrepreneurship", "current_situation": "Final-year BS student working part-time", "preferred_language": "English", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "Data scientist in a product company", "interest_area_ids": [2]}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"career_goal": "Entrepreneurship", "interest_area_ids": [2]}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"career_goal": "Entrepreneurship", "current_situation": "Final-year BS student working part-time", "preferred_language": "English", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "Data scientist in a product company", "interest_area_ids": [2], "id": 1, "user_id": 1}`

**Result:** Success

pytest: `tests/test_api_students.py::test_update_profile_replaces_previous_values`

---

### TC-044: Only the first 5 interest areas are kept

**User stories:** US-04

The student story allows up to 5 interest areas; extra ones are dropped.

**API being tested:** `PUT /api/v1/students/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <student token>`
- JSON: `{"career_goal": "Job", "current_situation": "Final-year BS student working part-time", "preferred_language": "English", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "Data scientist in a product company", "interest_area_ids": [1, 2, 3, 4, 5, 6]}`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"career_goal": "Job", "current_situation": "Final-year BS student working part-time", "preferred_language": "English", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "Data scientist in a product company", "interest_area_ids": [1, 2, 3, 4, 5], "id": 1, "user_id": 1}`

**Result:** Success

pytest: `tests/test_api_students.py::test_profile_keeps_only_first_five_interests`

---

### TC-045: Interest ids that do not exist are ignored

**User stories:** US-04

**API being tested:** `PUT /api/v1/students/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <student token>`
- JSON: `{"career_goal": "Job", "current_situation": "Final-year BS student working part-time", "preferred_language": "English", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "Data scientist in a product company", "interest_area_ids": [1, 9999]}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"interest_area_ids": [1]}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"career_goal": "Job", "current_situation": "Final-year BS student working part-time", "preferred_language": "English", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "Data scientist in a product company", "interest_area_ids": [1], "id": 1, "user_id": 1}`

**Result:** Success

pytest: `tests/test_api_students.py::test_profile_ignores_unknown_interest_ids`

---

### TC-046: Profile text longer than its limit is rejected with 422 [career_goal-1000]

**User stories:** US-04

**API being tested:** `PUT /api/v1/students/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <student token>`
- JSON: `{"career_goal": "<1001 characters: 'xxxxxxxxxxxx'...>", "current_situation": "Final-year BS student working part-time", "preferred_language": "English", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "Data scientist in a product company", "interest_area_ids": []}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_long", "loc": ["body", "career_goal"], "msg": "String should have at most 1000 characters", "input": "<1001 characters: 'xxxxxxxxxxxx'...>", "ctx": {"max_length": 1000}}]}`

**Result:** Success

pytest: `tests/test_api_students.py::test_profile_rejects_overlong_fields[career_goal-1000]`

---

### TC-047: Profile text longer than its limit is rejected with 422 [current_situation-1000]

**User stories:** US-04

**API being tested:** `PUT /api/v1/students/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <student token>`
- JSON: `{"career_goal": "Job", "current_situation": "<1001 characters: 'xxxxxxxxxxxx'...>", "preferred_language": "English", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "Data scientist in a product company", "interest_area_ids": []}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_long", "loc": ["body", "current_situation"], "msg": "String should have at most 1000 characters", "input": "<1001 characters: 'xxxxxxxxxxxx'...>", "ctx": {"max_length": 1000}}]}`

**Result:** Success

pytest: `tests/test_api_students.py::test_profile_rejects_overlong_fields[current_situation-1000]`

---

### TC-048: Profile text longer than its limit is rejected with 422 [preferred_language-100]

**User stories:** US-04

**API being tested:** `PUT /api/v1/students/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <student token>`
- JSON: `{"career_goal": "Job", "current_situation": "Final-year BS student working part-time", "preferred_language": "<101 characters: 'xxxxxxxxxxxx'...>", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "Data scientist in a product company", "interest_area_ids": []}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_long", "loc": ["body", "preferred_language"], "msg": "String should have at most 100 characters", "input": "<101 characters: 'xxxxxxxxxxxx'...>", "ctx": {"max_length": 100}}]}`

**Result:** Success

pytest: `tests/test_api_students.py::test_profile_rejects_overlong_fields[preferred_language-100]`

---

### TC-049: Profile text longer than its limit is rejected with 422 [weekly_availability-1000]

**User stories:** US-04

**API being tested:** `PUT /api/v1/students/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <student token>`
- JSON: `{"career_goal": "Job", "current_situation": "Final-year BS student working part-time", "preferred_language": "English", "weekly_availability": "<1001 characters: 'xxxxxxxxxxxx'...>", "career_aspirations": "Data scientist in a product company", "interest_area_ids": []}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_long", "loc": ["body", "weekly_availability"], "msg": "String should have at most 1000 characters", "input": "<1001 characters: 'xxxxxxxxxxxx'...>", "ctx": {"max_length": 1000}}]}`

**Result:** Success

pytest: `tests/test_api_students.py::test_profile_rejects_overlong_fields[weekly_availability-1000]`

---

### TC-050: Profile text longer than its limit is rejected with 422 [career_aspirations-2000]

**User stories:** US-04

**API being tested:** `PUT /api/v1/students/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <student token>`
- JSON: `{"career_goal": "Job", "current_situation": "Final-year BS student working part-time", "preferred_language": "English", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "<2001 characters: 'xxxxxxxxxxxx'...>", "interest_area_ids": []}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_long", "loc": ["body", "career_aspirations"], "msg": "String should have at most 2000 characters", "input": "<2001 characters: 'xxxxxxxxxxxx'...>", "ctx": {"max_length": 2000}}]}`

**Result:** Success

pytest: `tests/test_api_students.py::test_profile_rejects_overlong_fields[career_aspirations-2000]`

---

### TC-051: An administrator cannot create a student profile

**User stories:** US-04

**API being tested:** `PUT /api/v1/students/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"career_goal": "Job", "current_situation": "Final-year BS student working part-time", "preferred_language": "English", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "Data scientist in a product company", "interest_area_ids": []}`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Student access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Student access required"}`

**Result:** Success

pytest: `tests/test_api_students.py::test_profile_update_forbidden_for_admin`

---

### TC-052: Each profile change is kept with its date

**User stories:** US-06

**API being tested:** `PUT /api/v1/students/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <student token>`
- JSON: `{"career_goal": "Research", "current_situation": "Final-year BS student working part-time", "preferred_language": "English", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "Data scientist in a product company", "interest_area_ids": []}`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"career_goal": "Research", "current_situation": "Final-year BS student working part-time", "preferred_language": "English", "weekly_availability": "Weekends, 2 hours", "career_aspirations": "Data scientist in a product company", "interest_area_ids": [], "id": 1, "user_id": 1}`

**Result:** Fail

> **Defect found:** US-06 asks for each profile change to be saved with a date; profile_history is never written and no change log exists.

pytest: `tests/test_api_students.py::test_profile_change_is_saved_with_a_date`

---

### TC-053: A student adds a career question (50-500 characters)

**User stories:** US-05

**API being tested:** `POST /api/v1/students/questions`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"question_text": "How should I prepare for data science interviews in my final term of the BS degree?"}`

**Expected Output:**
- HTTP Status Code: 201
- JSON containing: `{"question_text": "How should I prepare for data science interviews in my final term of the BS degree?"}`

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"question_text": "How should I prepare for data science interviews in my final term of the BS degree?", "id": 1, "created_at": "2026-11-17T17:08:09.781325"}`

**Result:** Success

pytest: `tests/test_api_students.py::test_create_career_question`

---

### TC-054: Career questions of exactly 50 and 500 characters are accepted [exactly-50]

**User stories:** US-05

**API being tested:** `POST /api/v1/students/questions`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"question_text": "qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq"}`

**Expected Output:**
- HTTP Status Code: 201

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"question_text": "qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq", "id": 1, "created_at": "2026-11-17T17:08:09.855216"}`

**Result:** Success

pytest: `tests/test_api_students.py::test_career_question_length_boundaries_accepted[exactly-50]`

---

### TC-055: Career questions of exactly 50 and 500 characters are accepted [exactly-500]

**User stories:** US-05

**API being tested:** `POST /api/v1/students/questions`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"question_text": "<500 characters: 'qqqqqqqqqqqq'...>"}`

**Expected Output:**
- HTTP Status Code: 201

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"question_text": "<500 characters: 'qqqqqqqqqqqq'...>", "id": 1, "created_at": "2026-11-17T17:08:09.935028"}`

**Result:** Success

pytest: `tests/test_api_students.py::test_career_question_length_boundaries_accepted[exactly-500]`

---

### TC-056: Career questions of 49 or 501 characters are rejected [49-chars]

**User stories:** US-05

**API being tested:** `POST /api/v1/students/questions`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"question_text": "qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_short", "loc": ["body", "question_text"], "msg": "String should have at least 50 characters", "input": "qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq", "ctx": {"min_length": 50}}]}`

**Result:** Success

pytest: `tests/test_api_students.py::test_career_question_length_boundaries_rejected[49-chars]`

---

### TC-057: Career questions of 49 or 501 characters are rejected [501-chars]

**User stories:** US-05

**API being tested:** `POST /api/v1/students/questions`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"question_text": "<501 characters: 'qqqqqqqqqqqq'...>"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_long", "loc": ["body", "question_text"], "msg": "String should have at most 500 characters", "input": "<501 characters: 'qqqqqqqqqqqq'...>", "ctx": {"max_length": 500}}]}`

**Result:** Success

pytest: `tests/test_api_students.py::test_career_question_length_boundaries_rejected[501-chars]`

---

### TC-058: A mentor cannot post a career question

**User stories:** US-05

**API being tested:** `POST /api/v1/students/questions`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"question_text": "qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq"}`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Student access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Student access required"}`

**Result:** Success

pytest: `tests/test_api_students.py::test_career_question_forbidden_for_mentor`

---

### TC-059: A career question cannot be posted without logging in

**User stories:** US-05

**API being tested:** `POST /api/v1/students/questions`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"question_text": "qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq"}`

**Expected Output:**
- HTTP Status Code: 401

**Actual Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Not authenticated"}`

**Result:** Success

pytest: `tests/test_api_students.py::test_career_question_requires_login`

---

### TC-060: A student's questions are listed newest first

**User stories:** US-05

**API being tested:** `GET /api/v1/students/questions`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `[{"question_text": "Second question bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "id": 2, "created_at": "2026-11-17T17:08:10.259198"}, {"question_text": "First question aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "id": 1, "created_at": "2026-11-17T16:08:10.241355"}]`

**Result:** Success

pytest: `tests/test_api_students.py::test_list_career_questions_newest_first`

---

### TC-061: A student only sees their own questions

**User stories:** US-05

**API being tested:** `GET /api/v1/students/questions`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 200
- JSON: `[]`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `[]`

**Result:** Success

pytest: `tests/test_api_students.py::test_list_career_questions_only_own`

---

### TC-062: A mentor cannot list career questions

**User stories:** US-05

**API being tested:** `GET /api/v1/students/questions`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <mentor token>`

**Expected Output:**
- HTTP Status Code: 403

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Student access required"}`

**Result:** Success

pytest: `tests/test_api_students.py::test_list_career_questions_forbidden_for_mentor`

---

## Mentor applications, profiles, search and public profiles

Source: `backend/tests/test_api_mentors.py`

### TC-063: A graduate applies as a mentor with roll number, graduation year and LinkedIn URL

**User stories:** US-02

**API being tested:** `POST /api/v1/mentors/apply`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"roll_number": "21f1000123", "graduation_year": 2025, "linked_in_url": "https://www.linkedin.com/in/ravi-kumar"}`

**Expected Output:**
- HTTP Status Code: 201
- JSON containing: `{"roll_number": "21f1000123", "graduation_year": 2025, "linked_in_url": "https://www.linkedin.com/in/ravi-kumar", "status": "pending", "user_id": 1, "admin_decision": null}`

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"roll_number": "21f1000123", "graduation_year": 2025, "linked_in_url": "https://www.linkedin.com/in/ravi-kumar", "additional_verification_info": null, "id": 1, "user_id": 1, "status": "pending", "admin_decision": null, "rejection_reason": null, "submitted_at": "2026-11-17T17:07:28.993357", "decision_at": null}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_apply_as_mentor_with_roll_number_year_and_linkedin`

---

### TC-064: A mentor cannot submit a second application

**User stories:** US-02

**API being tested:** `POST /api/v1/mentors/apply`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"roll_number": "21f1000999"}`

**Expected Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "Application already submitted"}`

**Actual Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "Application already submitted"}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_apply_twice_is_rejected`

---

### TC-065: A student cannot apply through the mentor application endpoint

**User stories:** US-02

**API being tested:** `POST /api/v1/mentors/apply`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"roll_number": "21f1000001"}`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Mentor role required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Mentor role required"}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_apply_forbidden_for_student`

---

### TC-066: An application with an impossible graduation year is rejected [1949]

**User stories:** US-02

**API being tested:** `POST /api/v1/mentors/apply`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"graduation_year": 1949}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "greater_than_equal", "loc": ["body", "graduation_year"], "msg": "Input should be greater than or equal to 1950", "input": 1949, "ctx": {"ge": 1950}}]}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_apply_rejects_impossible_graduation_year[1949]`

---

### TC-067: An application with an impossible graduation year is rejected [2101]

**User stories:** US-02

**API being tested:** `POST /api/v1/mentors/apply`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"graduation_year": 2101}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "less_than_equal", "loc": ["body", "graduation_year"], "msg": "Input should be less than or equal to 2100", "input": 2101, "ctx": {"le": 2100}}]}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_apply_rejects_impossible_graduation_year[2101]`

---

### TC-068: A mentor application cannot be sent without logging in

**User stories:** US-02

**API being tested:** `POST /api/v1/mentors/apply`

**Inputs:**
- Request Method: POST
- Header: none (not logged in)
- JSON: `{"roll_number": "21f1000001"}`

**Expected Output:**
- HTTP Status Code: 401

**Actual Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Not authenticated"}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_apply_requires_login`

---

### TC-069: An application without roll number, graduation year or LinkedIn should be rejected

**User stories:** US-02

**API being tested:** `POST /api/v1/mentors/apply`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"roll_number": null, "graduation_year": null, "linked_in_url": null, "additional_verification_info": null, "id": 1, "user_id": 1, "status": "pending", "admin_decision": null, "rejection_reason": null, "submitted_at": "2026-11-17T17:07:29.348172", "decision_at": null}`

**Result:** Fail

> **Defect found:** US-02 requires roll number, graduation year and LinkedIn URL, but all three are optional: an empty application is accepted.

pytest: `tests/test_api_mentors.py::test_apply_requires_verification_details`

---

### TC-070: An approved mentor reads their profile and current mentee count

**User stories:** US-07, US-08

**API being tested:** `GET /api/v1/mentors/me/profile`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <mentor token>`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"user_id": 1, "status": "approved", "max_mentee_capacity": 2, "current_mentee_count": 0}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"career_history": null, "organisations": null, "roles": null, "years_of_experience": 0, "graduation_year": null, "experience_level": "Recent Graduate", "guidance_types": "Career mentoring", "preferred_languages": "English", "max_mentee_capacity": 2, "availability": null, "pause_status": "active", "expertise_area_ids": [], "id": 1, "user_id": 1, "status": "approved", "current_mentee_count": 0}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_get_mentor_profile_after_approval`

---

### TC-071: The mentee count goes up when a request is accepted

**User stories:** US-08, US-15

**API being tested:** `GET /api/v1/mentors/me/profile`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <mentor token>`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"current_mentee_count": 1}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"career_history": null, "organisations": null, "roles": null, "years_of_experience": 0, "graduation_year": null, "experience_level": "Recent Graduate", "guidance_types": "Career mentoring", "preferred_languages": "English", "max_mentee_capacity": 3, "availability": null, "pause_status": "active", "expertise_area_ids": [], "id": 1, "user_id": 1, "status": "approved", "current_mentee_count": 1}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_get_mentor_profile_counts_active_mentees`

---

### TC-072: A mentor who has not been approved or set up a profile gets 404

**User stories:** US-07

**API being tested:** `GET /api/v1/mentors/me/profile`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <mentor token>`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Mentor profile not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Mentor profile not found"}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_get_mentor_profile_before_it_exists`

---

### TC-073: A student cannot use the mentor profile endpoint

**User stories:** US-07

**API being tested:** `GET /api/v1/mentors/me/profile`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Mentor access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Mentor access required"}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_get_mentor_profile_forbidden_for_student`

---

### TC-074: A mentor saves career path, expertise and guidance types

**User stories:** US-07

**API being tested:** `PUT /api/v1/mentors/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"career_history": "Analyst at Infosys (2 years), now Data Scientist at Flipkart", "organisations": "Infosys, Flipkart", "roles": "Data Scientist", "years_of_experience": 3, "graduation_year": 2023, "experience_level": "Experienced", "guidance_types": "Job, Higher Studies", "preferred_languages": "English, Tamil", "max_mentee_capacity": 3, "availability": "Weekday evenings", "pause_status": "active", "expertise_area_ids": [1, 2]}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"career_history": "Analyst at Infosys (2 years), now Data Scientist at Flipkart", "organisations": "Infosys, Flipkart", "roles": "Data Scientist", "years_of_experience": 3, "graduation_year": 2023, "experience_level": "Experienced", "guidance_types": "Job, Higher Studies", "preferred_languages": "English, Tamil", "max_mentee_capacity": 3, "availability": "Weekday evenings", "pause_status": "active", "expertise_area_ids": [1, 2], "status": "approved"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"career_history": "Analyst at Infosys (2 years), now Data Scientist at Flipkart", "organisations": "Infosys, Flipkart", "roles": "Data Scientist", "years_of_experience": 3, "graduation_year": 2023, "experience_level": "Experienced", "guidance_types": "Job, Higher Studies", "preferred_languages": "English, Tamil", "max_mentee_capacity": 3, "availability": "Weekday evenings", "pause_status": "active", "expertise_area_ids": [1, 2], "id": 1, "user_id": 1, "status": "approved", "current_mentee_count": 0}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_update_mentor_profile_career_path_and_expertise`

---

### TC-075: Mentee capacity of 1 and 5 is accepted [min-1]

**User stories:** US-08

**API being tested:** `PUT /api/v1/mentors/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"career_history": "Analyst at Infosys (2 years), now Data Scientist at Flipkart", "organisations": "Infosys, Flipkart", "roles": "Data Scientist", "years_of_experience": 3, "graduation_year": 2023, "experience_level": "Experienced", "guidance_types": "Job, Higher Studies", "preferred_languages": "English, Tamil", "max_mentee_capacity": 1, "availability": "Weekday evenings", "pause_status": "active", "expertise_area_ids": []}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"max_mentee_capacity": 1}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"career_history": "Analyst at Infosys (2 years), now Data Scientist at Flipkart", "organisations": "Infosys, Flipkart", "roles": "Data Scientist", "years_of_experience": 3, "graduation_year": 2023, "experience_level": "Experienced", "guidance_types": "Job, Higher Studies", "preferred_languages": "English, Tamil", "max_mentee_capacity": 1, "availability": "Weekday evenings", "pause_status": "active", "expertise_area_ids": [], "id": 1, "user_id": 1, "status": "approved", "current_mentee_count": 0}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_mentor_capacity_bounds_accepted[min-1]`

---

### TC-076: Mentee capacity of 1 and 5 is accepted [max-5]

**User stories:** US-08

**API being tested:** `PUT /api/v1/mentors/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"career_history": "Analyst at Infosys (2 years), now Data Scientist at Flipkart", "organisations": "Infosys, Flipkart", "roles": "Data Scientist", "years_of_experience": 3, "graduation_year": 2023, "experience_level": "Experienced", "guidance_types": "Job, Higher Studies", "preferred_languages": "English, Tamil", "max_mentee_capacity": 5, "availability": "Weekday evenings", "pause_status": "active", "expertise_area_ids": []}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"max_mentee_capacity": 5}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"career_history": "Analyst at Infosys (2 years), now Data Scientist at Flipkart", "organisations": "Infosys, Flipkart", "roles": "Data Scientist", "years_of_experience": 3, "graduation_year": 2023, "experience_level": "Experienced", "guidance_types": "Job, Higher Studies", "preferred_languages": "English, Tamil", "max_mentee_capacity": 5, "availability": "Weekday evenings", "pause_status": "active", "expertise_area_ids": [], "id": 1, "user_id": 1, "status": "approved", "current_mentee_count": 0}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_mentor_capacity_bounds_accepted[max-5]`

---

### TC-077: Mentee capacity of 0 or 6 is rejected [zero]

**User stories:** US-08

**API being tested:** `PUT /api/v1/mentors/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"career_history": "Analyst at Infosys (2 years), now Data Scientist at Flipkart", "organisations": "Infosys, Flipkart", "roles": "Data Scientist", "years_of_experience": 3, "graduation_year": 2023, "experience_level": "Experienced", "guidance_types": "Job, Higher Studies", "preferred_languages": "English, Tamil", "max_mentee_capacity": 0, "availability": "Weekday evenings", "pause_status": "active", "expertise_area_ids": []}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "greater_than_equal", "loc": ["body", "max_mentee_capacity"], "msg": "Input should be greater than or equal to 1", "input": 0, "ctx": {"ge": 1}}]}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_mentor_capacity_out_of_range_rejected[zero]`

---

### TC-078: Mentee capacity of 0 or 6 is rejected [six]

**User stories:** US-08

**API being tested:** `PUT /api/v1/mentors/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"career_history": "Analyst at Infosys (2 years), now Data Scientist at Flipkart", "organisations": "Infosys, Flipkart", "roles": "Data Scientist", "years_of_experience": 3, "graduation_year": 2023, "experience_level": "Experienced", "guidance_types": "Job, Higher Studies", "preferred_languages": "English, Tamil", "max_mentee_capacity": 6, "availability": "Weekday evenings", "pause_status": "active", "expertise_area_ids": []}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "less_than_equal", "loc": ["body", "max_mentee_capacity"], "msg": "Input should be less than or equal to 5", "input": 6, "ctx": {"le": 5}}]}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_mentor_capacity_out_of_range_rejected[six]`

---

### TC-079: Negative years of experience are rejected

**User stories:** US-07

**API being tested:** `PUT /api/v1/mentors/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"career_history": "Analyst at Infosys (2 years), now Data Scientist at Flipkart", "organisations": "Infosys, Flipkart", "roles": "Data Scientist", "years_of_experience": -1, "graduation_year": 2023, "experience_level": "Experienced", "guidance_types": "Job, Higher Studies", "preferred_languages": "English, Tamil", "max_mentee_capacity": 3, "availability": "Weekday evenings", "pause_status": "active", "expertise_area_ids": []}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "greater_than_equal", "loc": ["body", "years_of_experience"], "msg": "Input should be greater than or equal to 0", "input": -1, "ctx": {"ge": 0}}]}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_mentor_profile_rejects_negative_experience`

---

### TC-080: A mentor pauses and disappears from search

**User stories:** US-08, US-09

**API being tested:** `PUT /api/v1/mentors/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"career_history": "Analyst at Infosys (2 years), now Data Scientist at Flipkart", "organisations": "Infosys, Flipkart", "roles": "Data Scientist", "years_of_experience": 3, "graduation_year": 2023, "experience_level": "Experienced", "guidance_types": "Job, Higher Studies", "preferred_languages": "English, Tamil", "max_mentee_capacity": 3, "availability": "Weekday evenings", "pause_status": "paused", "expertise_area_ids": []}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"pause_status": "paused"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"career_history": "Analyst at Infosys (2 years), now Data Scientist at Flipkart", "organisations": "Infosys, Flipkart", "roles": "Data Scientist", "years_of_experience": 3, "graduation_year": 2023, "experience_level": "Experienced", "guidance_types": "Job, Higher Studies", "preferred_languages": "English, Tamil", "max_mentee_capacity": 3, "availability": "Weekday evenings", "pause_status": "paused", "expertise_area_ids": [], "id": 1, "user_id": 1, "status": "approved", "current_mentee_count": 0}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_mentor_can_pause`

---

### TC-081: A student cannot update a mentor profile

**User stories:** US-07

**API being tested:** `PUT /api/v1/mentors/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <student token>`
- JSON: `{"career_history": "Analyst at Infosys (2 years), now Data Scientist at Flipkart", "organisations": "Infosys, Flipkart", "roles": "Data Scientist", "years_of_experience": 3, "graduation_year": 2023, "experience_level": "Experienced", "guidance_types": "Job, Higher Studies", "preferred_languages": "English, Tamil", "max_mentee_capacity": 3, "availability": "Weekday evenings", "pause_status": "active", "expertise_area_ids": []}`

**Expected Output:**
- HTTP Status Code: 403

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Mentor access required"}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_mentor_profile_update_forbidden_for_student`

---

### TC-082: An unknown pause status should be rejected with 422

**User stories:** US-08

**API being tested:** `PUT /api/v1/mentors/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"career_history": "Analyst at Infosys (2 years), now Data Scientist at Flipkart", "organisations": "Infosys, Flipkart", "roles": "Data Scientist", "years_of_experience": 3, "graduation_year": 2023, "experience_level": "Experienced", "guidance_types": "Job, Higher Studies", "preferred_languages": "English, Tamil", "max_mentee_capacity": 3, "availability": "Weekday evenings", "pause_status": "holiday", "expertise_area_ids": []}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 500
- JSON: `"Internal Server Error"`

**Result:** Fail

> **Defect found:** pause_status is not validated by the schema; an unknown value hits the database CHECK constraint and returns 500 instead of 422.

pytest: `tests/test_api_mentors.py::test_mentor_profile_rejects_unknown_pause_status`

---

### TC-083: An unknown experience level should be rejected with 422

**User stories:** US-07

**API being tested:** `PUT /api/v1/mentors/me/profile`

**Inputs:**
- Request Method: PUT
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"career_history": "Analyst at Infosys (2 years), now Data Scientist at Flipkart", "organisations": "Infosys, Flipkart", "roles": "Data Scientist", "years_of_experience": 3, "graduation_year": 2023, "experience_level": "Guru", "guidance_types": "Job, Higher Studies", "preferred_languages": "English, Tamil", "max_mentee_capacity": 3, "availability": "Weekday evenings", "pause_status": "active", "expertise_area_ids": []}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 500
- JSON: `"Internal Server Error"`

**Result:** Fail

> **Defect found:** experience_level is not validated by the schema; an unknown value hits the database CHECK constraint and returns 500 instead of 422.

pytest: `tests/test_api_mentors.py::test_mentor_profile_rejects_unknown_experience_level`

---

### TC-084: Mentor search filters by domain, guidance type, industry, graduation year and language [no-filter]

**User stories:** US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"total": 3}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "user_id": 1, "name": "Anita Data", "experience_level": "Senior", "roles": "Data Scientist", "organisations": "Google", "preferred_languages": "English, Hindi", "guidance_types": "Job", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}, {"id": 2, "user_id": 3, "name": "Bala Research", "experience_level": "Recent Graduate", "roles": "PhD Scholar", "organisations": "IISc", "preferred_languages": "Tamil", "guidance_types": "Research, Higher Studies", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}, {"id": 3, "user_id": 4, "name": "Chitra Startup", "experience_level": "Experienced", "roles": "Founder", "organisations": "Own startup", "preferred_languages": "English", "guidance_types": "Entrepreneurship", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}], "page": 1, "page_size": 10, "total": 3}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_filters[no-filter]`

---

### TC-085: Mentor search filters by domain, guidance type, industry, graduation year and language [by-role]

**User stories:** US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"query": "founder"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"total": 1}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 3, "user_id": 4, "name": "Chitra Startup", "experience_level": "Experienced", "roles": "Founder", "organisations": "Own startup", "preferred_languages": "English", "guidance_types": "Entrepreneurship", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}], "page": 1, "page_size": 10, "total": 1}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_filters[by-role]`

---

### TC-086: Mentor search filters by domain, guidance type, industry, graduation year and language [by-name]

**User stories:** US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"query": "bala"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"total": 1}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 2, "user_id": 3, "name": "Bala Research", "experience_level": "Recent Graduate", "roles": "PhD Scholar", "organisations": "IISc", "preferred_languages": "Tamil", "guidance_types": "Research, Higher Studies", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}], "page": 1, "page_size": 10, "total": 1}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_filters[by-name]`

---

### TC-087: Mentor search filters by domain, guidance type, industry, graduation year and language [by-domain]

**User stories:** US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"domain": "google"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"total": 1}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "user_id": 1, "name": "Anita Data", "experience_level": "Senior", "roles": "Data Scientist", "organisations": "Google", "preferred_languages": "English, Hindi", "guidance_types": "Job", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}], "page": 1, "page_size": 10, "total": 1}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_filters[by-domain]`

---

### TC-088: Mentor search filters by domain, guidance type, industry, graduation year and language [by-industry]

**User stories:** US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"industry": "startup"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"total": 1}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 3, "user_id": 4, "name": "Chitra Startup", "experience_level": "Experienced", "roles": "Founder", "organisations": "Own startup", "preferred_languages": "English", "guidance_types": "Entrepreneurship", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}], "page": 1, "page_size": 10, "total": 1}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_filters[by-industry]`

---

### TC-089: Mentor search filters by domain, guidance type, industry, graduation year and language [by-guidance]

**User stories:** US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"guidance_type": "higher studies"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"total": 1}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 2, "user_id": 3, "name": "Bala Research", "experience_level": "Recent Graduate", "roles": "PhD Scholar", "organisations": "IISc", "preferred_languages": "Tamil", "guidance_types": "Research, Higher Studies", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}], "page": 1, "page_size": 10, "total": 1}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_filters[by-guidance]`

---

### TC-090: Mentor search filters by domain, guidance type, industry, graduation year and language [by-language]

**User stories:** US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"language": "english"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"total": 2}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "user_id": 1, "name": "Anita Data", "experience_level": "Senior", "roles": "Data Scientist", "organisations": "Google", "preferred_languages": "English, Hindi", "guidance_types": "Job", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}, {"id": 3, "user_id": 4, "name": "Chitra Startup", "experience_level": "Experienced", "roles": "Founder", "organisations": "Own startup", "preferred_languages": "English", "guidance_types": "Entrepreneurship", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}], "page": 1, "page_size": 10, "total": 2}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_filters[by-language]`

---

### TC-091: Mentor search filters by domain, guidance type, industry, graduation year and language [by-year]

**User stories:** US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"graduation_year": 2022}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"total": 2}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "user_id": 1, "name": "Anita Data", "experience_level": "Senior", "roles": "Data Scientist", "organisations": "Google", "preferred_languages": "English, Hindi", "guidance_types": "Job", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}, {"id": 3, "user_id": 4, "name": "Chitra Startup", "experience_level": "Experienced", "roles": "Founder", "organisations": "Own startup", "preferred_languages": "English", "guidance_types": "Entrepreneurship", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}], "page": 1, "page_size": 10, "total": 2}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_filters[by-year]`

---

### TC-092: Mentor search filters by domain, guidance type, industry, graduation year and language [by-level]

**User stories:** US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"experience_level": "Senior"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"total": 1}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "user_id": 1, "name": "Anita Data", "experience_level": "Senior", "roles": "Data Scientist", "organisations": "Google", "preferred_languages": "English, Hindi", "guidance_types": "Job", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}], "page": 1, "page_size": 10, "total": 1}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_filters[by-level]`

---

### TC-093: Mentor search filters by domain, guidance type, industry, graduation year and language [combined]

**User stories:** US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"language": "english", "guidance_type": "job"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"total": 1}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "user_id": 1, "name": "Anita Data", "experience_level": "Senior", "roles": "Data Scientist", "organisations": "Google", "preferred_languages": "English, Hindi", "guidance_types": "Job", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}], "page": 1, "page_size": 10, "total": 1}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_filters[combined]`

---

### TC-094: Mentor search filters by domain, guidance type, industry, graduation year and language [no-match]

**User stories:** US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"query": "nobody-matches"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"total": 0}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [], "page": 1, "page_size": 10, "total": 0}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_filters[no-match]`

---

### TC-095: Search shows only approved, active mentors with free capacity

**User stories:** US-08, US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"query": "Zed"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"total": 1}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 3, "user_id": 6, "name": "Zed Open", "experience_level": "Recent Graduate", "roles": null, "organisations": null, "preferred_languages": "English", "guidance_types": "Career mentoring", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}], "page": 1, "page_size": 10, "total": 1}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_hides_unapproved_paused_and_full_mentors`

---

### TC-096: A suspended mentor does not appear in search

**User stories:** US-09, US-24

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"query": "Suspended Sam"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"total": 0}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [], "page": 1, "page_size": 10, "total": 0}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_hides_suspended_mentor`

---

### TC-097: Search returns results page by page

**User stories:** US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"page": 2, "page_size": 2}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"page": 2, "page_size": 2, "total": 3}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 3, "user_id": 4, "name": "Chitra Startup", "experience_level": "Experienced", "roles": "Founder", "organisations": "Own startup", "preferred_languages": "English", "guidance_types": "Entrepreneurship", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}], "page": 2, "page_size": 2, "total": 3}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_pagination`

---

### TC-098: Search rejects page 0 and page sizes outside 1-50 [page-0]

**User stories:** US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"page": 0}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "greater_than_equal", "loc": ["query", "page"], "msg": "Input should be greater than or equal to 1", "input": "0", "ctx": {"ge": 1}}]}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_rejects_bad_paging[page-0]`

---

### TC-099: Search rejects page 0 and page sizes outside 1-50 [page-size-0]

**User stories:** US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"page_size": 0}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "greater_than_equal", "loc": ["query", "page_size"], "msg": "Input should be greater than or equal to 1", "input": "0", "ctx": {"ge": 1}}]}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_rejects_bad_paging[page-size-0]`

---

### TC-100: Search rejects page 0 and page sizes outside 1-50 [page-size-51]

**User stories:** US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"page_size": 51}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "less_than_equal", "loc": ["query", "page_size"], "msg": "Input should be less than or equal to 50", "input": "51", "ctx": {"le": 50}}]}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_rejects_bad_paging[page-size-51]`

---

### TC-101: Search results do not show email addresses

**User stories:** US-11

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"query": "Private"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"total": 1}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "user_id": 1, "name": "Private Priya", "experience_level": "Recent Graduate", "roles": null, "organisations": null, "preferred_languages": "English", "guidance_types": "Career mentoring", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}], "page": 1, "page_size": 10, "total": 1}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_result_hides_contact_details`

---

### TC-102: Search over 200 mentors with filters answers in under 2 seconds

**User stories:** US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)
- Query: `{"domain": "TCS", "language": "English", "page_size": 50}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"total": 100}`
- Also: response time under 2 seconds

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 2, "user_id": 2, "name": "Bulk Mentor 001", "experience_level": "Recent Graduate", "roles": null, "organisations": "TCS", "preferred_languages": "English", "guidance_types": "Job", "status": "approved", "max_mentee_capacity": 3, "current_mentee_count": 0}, {"id": 4, "user_id": 4, "name": "Bulk Mentor 003", "experience_level": "Recent Graduate", "roles": null, "organisations": "TCS", "preferred_languages": "English", "guidance_types": "Job", "status": "approved", "max_mentee_capacity": 3, "current_mentee_count": 0}, {"id": 6, "user_id": 6, "name": "Bulk Mentor 005", "experience_level": "Recent Graduate", "roles": null, "organisations": "TCS", "preferred_languages": "English", "guidance_types": "Job", "status": "approved", "max_mentee_capacity": 3, "current_mentee_count": 0}, {"id": 8, "user_id": 8, "name": "Bulk Mentor 007", "experience_level": "Recent Graduate", "roles": null, "organisations": "TCS", "preferred_languages": "English", "guidance_types": "Job", "status": "approved", "max_mentee_capacity": 3, "current_mentee_count": 0}, {"id": 10, "user_id": 10, "name": "Bulk Mentor 009", "experience_level": "Recent Graduate", "roles": null, "organisations": "TCS", "preferred_languages": "English", "guidance_types": "Job", "status": "approved", "max_mentee_capacity": 3, "current_mentee_count": 0}, "... 45 more items"], "page": 1, "page_size": 50, "total": 100}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_search_responds_within_two_seconds`

---

### TC-103: Mentor search should require a logged-in user

**User stories:** US-01, US-09

**API being tested:** `GET /api/v1/mentors/search`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)

**Expected Output:**
- HTTP Status Code: 401

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "user_id": 1, "name": "Mentor 1", "experience_level": "Recent Graduate", "roles": null, "organisations": null, "preferred_languages": "English", "guidance_types": "Career mentoring", "status": "approved", "max_mentee_capacity": 1, "current_mentee_count": 0}], "page": 1, "page_size": 10, "total": 1}`

**Result:** Fail

> **Defect found:** Mentor search is public: it works without logging in, although US-01 limits the platform to verified students.

pytest: `tests/test_api_mentors.py::test_search_requires_login`

---

### TC-104: A student views an approved mentor's public profile

**User stories:** US-11

**API being tested:** `GET /api/v1/mentors/1`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"id": 1, "name": "Deepa Nair", "organisations": "Infosys, Flipkart", "roles": "Data Scientist"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "name": "Deepa Nair", "career_history": "Analyst at Infosys (2 years), now Data Scientist at Flipkart", "organisations": "Infosys, Flipkart", "roles": "Data Scientist", "years_of_experience": 3, "experience_level": "Experienced", "guidance_types": "Job, Higher Studies", "preferred_languages": "English, Tamil", "availability": "Weekday evenings", "max_mentee_capacity": 1, "match_score": 0, "match_explanation": []}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_public_profile_of_approved_mentor`

---

### TC-105: The public mentor profile does not show email or phone

**User stories:** US-11

**API being tested:** `GET /api/v1/mentors/1`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "name": "Mentor 1", "career_history": null, "organisations": null, "roles": null, "years_of_experience": 0, "experience_level": "Recent Graduate", "guidance_types": "Career mentoring", "preferred_languages": "English", "availability": null, "max_mentee_capacity": 1, "match_score": 0, "match_explanation": []}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_public_profile_hides_email_and_phone`

---

### TC-106: A mentor id that does not exist returns 404

**User stories:** US-11

**API being tested:** `GET /api/v1/mentors/9999`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Mentor not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Mentor not found"}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_public_profile_of_unknown_mentor`

---

### TC-107: An unapproved mentor's profile is not public

**User stories:** US-03, US-11

**API being tested:** `GET /api/v1/mentors/1`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Mentor not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Mentor not found"}`

**Result:** Success

pytest: `tests/test_api_mentors.py::test_public_profile_of_unapproved_mentor`

---

### TC-108: A suspended mentor's public profile should no longer be shown

**User stories:** US-11, US-24

**API being tested:** `GET /api/v1/mentors/1`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)

**Expected Output:**
- HTTP Status Code: 404

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "name": "Mentor 1", "career_history": null, "organisations": null, "roles": null, "years_of_experience": 0, "experience_level": "Recent Graduate", "guidance_types": "Career mentoring", "preferred_languages": "English", "availability": null, "max_mentee_capacity": 1, "match_score": 0, "match_explanation": []}`

**Result:** Fail

> **Defect found:** The public profile only checks the profile is approved, not that the user is active, so a suspended mentor's profile stays visible.

pytest: `tests/test_api_mentors.py::test_public_profile_hidden_after_suspension`

---

## Admin: mentor verification, dashboard and users

Source: `backend/tests/test_api_admin_applications.py`

### TC-109: An admin sees a submitted mentor application with its details

**User stories:** US-03

**API being tested:** `GET /api/v1/admin/applications`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `[{"roll_number": "21f2000456", "graduation_year": 2024, "linked_in_url": "https://www.linkedin.com/in/example", "additional_verification_info": null, "id": 1, "user_id": 1, "status": "pending", "admin_decision": null, "rejection_reason": null, "submitted_at": "2026-11-17T17:07:22.216046", "decision_at": null}]`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_list_applications_shows_pending_application`

---

### TC-110: A mentor cannot list mentor applications

**User stories:** US-03

**API being tested:** `GET /api/v1/admin/applications`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <mentor token>`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_list_applications_forbidden_for_mentor`

---

### TC-111: Mentor applications cannot be listed without logging in

**User stories:** US-03

**API being tested:** `GET /api/v1/admin/applications`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)

**Expected Output:**
- HTTP Status Code: 401

**Actual Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Not authenticated"}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_list_applications_requires_login`

---

### TC-112: Approving an application activates the mentor account and profile

**User stories:** US-03

**API being tested:** `POST /api/v1/admin/applications/1/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"action": "approve"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"id": 1, "status": "approved"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "approved", "decision_at": "2026-11-17T17:07:22.464965"}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_approve_application_activates_mentor`

---

### TC-113: Rejecting an application records the reason

**User stories:** US-03

**API being tested:** `POST /api/v1/admin/applications/1/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"action": "reject", "rejection_reason": "Roll number does not match our graduate records."}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"status": "rejected"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "rejected", "decision_at": "2026-11-17T17:07:22.591566"}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_reject_application_with_reason`

---

### TC-114: A rejected mentor stays pending verification and is not searchable

**User stories:** US-03

**API being tested:** `POST /api/v1/admin/applications/1/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"action": "reject", "rejection_reason": "Could not verify graduation."}`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "rejected", "decision_at": "2026-11-17T17:07:22.712639"}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_rejected_mentor_stays_unverified`

---

### TC-115: Rejecting without a reason of at least 5 characters is refused [missing]

**User stories:** US-03

**API being tested:** `POST /api/v1/admin/applications/1/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"action": "reject", "rejection_reason": null}`

**Expected Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "Rejection reason is required"}`

**Actual Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "Rejection reason is required"}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_reject_requires_reason[missing]`

---

### TC-116: Rejecting without a reason of at least 5 characters is refused [empty]

**User stories:** US-03

**API being tested:** `POST /api/v1/admin/applications/1/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"action": "reject", "rejection_reason": ""}`

**Expected Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "Rejection reason is required"}`

**Actual Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "Rejection reason is required"}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_reject_requires_reason[empty]`

---

### TC-117: Rejecting without a reason of at least 5 characters is refused [under-5-chars]

**User stories:** US-03

**API being tested:** `POST /api/v1/admin/applications/1/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"action": "reject", "rejection_reason": "no"}`

**Expected Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "Rejection reason is required"}`

**Actual Output:**
- HTTP Status Code: 400
- JSON: `{"detail": "Rejection reason is required"}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_reject_requires_reason[under-5-chars]`

---

### TC-118: A review action other than approve or reject is refused

**User stories:** US-03

**API being tested:** `POST /api/v1/admin/applications/1/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"action": "maybe"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_pattern_mismatch", "loc": ["body", "action"], "msg": "String should match pattern '^(approve|reject)$'", "input": "maybe", "ctx": {"pattern": "^(approve|reject)$"}}]}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_review_rejects_unknown_action`

---

### TC-119: Reviewing an application that does not exist returns 404

**User stories:** US-03

**API being tested:** `POST /api/v1/admin/applications/9999/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"action": "approve"}`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Application not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Application not found"}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_review_unknown_application`

---

### TC-120: A student cannot review mentor applications

**User stories:** US-03

**API being tested:** `POST /api/v1/admin/applications/1/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"action": "approve"}`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_review_forbidden_for_student`

---

### TC-121: A mentor cannot approve their own application

**User stories:** US-03

**API being tested:** `POST /api/v1/admin/applications/1/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"action": "approve"}`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_mentor_cannot_approve_own_application`

---

### TC-122: An application that was already approved cannot be reviewed again

**User stories:** US-03

**API being tested:** `POST /api/v1/admin/applications/1/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"action": "reject", "rejection_reason": "Changed my mind after approval."}`

**Expected Output:**
- HTTP Status Code: 409

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "rejected", "decision_at": "2026-11-17T17:07:23.562339"}`

**Result:** Fail

> **Defect found:** A decided application can be reviewed again. Rejecting after approval marks it rejected but leaves the mentor profile approved and searchable.

pytest: `tests/test_api_admin_applications.py::test_decided_application_cannot_be_reviewed_again`

---

### TC-123: The dashboard counts pending applications and approved mentors

**User stories:** US-21

**API being tested:** `GET /api/v1/admin/dashboard`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`

**Expected Output:**
- HTTP Status Code: 200
- JSON: `{"pending_applications": 2, "approved_mentors": 1, "recent_activity": []}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"pending_applications": 2, "approved_mentors": 1, "recent_activity": []}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_dashboard_counts_pending_and_approved`

---

### TC-124: A suspended mentor is not counted as an approved mentor

**User stories:** US-21, US-24

**API being tested:** `GET /api/v1/admin/dashboard`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"approved_mentors": 1}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"pending_applications": 0, "approved_mentors": 1, "recent_activity": []}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_dashboard_excludes_suspended_mentors`

---

### TC-125: A student cannot open the admin dashboard

**User stories:** US-21

**API being tested:** `GET /api/v1/admin/dashboard`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_dashboard_forbidden_for_student`

---

### TC-126: The admin dashboard cannot be opened without logging in

**User stories:** US-21

**API being tested:** `GET /api/v1/admin/dashboard`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)

**Expected Output:**
- HTTP Status Code: 401

**Actual Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Not authenticated"}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_dashboard_requires_login`

---

### TC-127: An admin lists all users with role and account status

**User stories:** US-21, US-24

**API being tested:** `GET /api/v1/admin/users`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"page": 1, "page_size": 50, "total": 3}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 3, "name": "Mentor 2", "role": "mentor", "account_status": "pending_verification"}, {"id": 2, "name": "Student 1", "role": "student", "account_status": "active"}, {"id": 1, "name": "Program Admin", "role": "admin", "account_status": "active"}], "page": 1, "page_size": 50, "total": 3}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_list_users_with_roles_and_status`

---

### TC-128: The user list is paged

**User stories:** US-21

**API being tested:** `GET /api/v1/admin/users`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`
- Query: `{"page": 2, "page_size": 3}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"total": 4, "page": 2}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "name": "Program Admin", "role": "admin", "account_status": "active"}], "page": 2, "page_size": 3, "total": 4}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_list_users_pagination`

---

### TC-129: Out-of-range paging values are clamped instead of failing [page-0]

**User stories:** US-21

**API being tested:** `GET /api/v1/admin/users`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`
- Query: `{"page": 0}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"page": 1}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "name": "Program Admin", "role": "admin", "account_status": "active"}], "page": 1, "page_size": 50, "total": 1}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_list_users_clamps_paging[page-0]`

---

### TC-130: Out-of-range paging values are clamped instead of failing [page-size-1000]

**User stories:** US-21

**API being tested:** `GET /api/v1/admin/users`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`
- Query: `{"page_size": 1000}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"page_size": 100}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "name": "Program Admin", "role": "admin", "account_status": "active"}], "page": 1, "page_size": 100, "total": 1}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_list_users_clamps_paging[page-size-1000]`

---

### TC-131: Out-of-range paging values are clamped instead of failing [page-size-0]

**User stories:** US-21

**API being tested:** `GET /api/v1/admin/users`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`
- Query: `{"page_size": 0}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"page_size": 1}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "name": "Program Admin", "role": "admin", "account_status": "active"}], "page": 1, "page_size": 1, "total": 1}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_list_users_clamps_paging[page-size-0]`

---

### TC-132: A mentor cannot list users

**User stories:** US-21

**API being tested:** `GET /api/v1/admin/users`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <mentor token>`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Result:** Success

pytest: `tests/test_api_admin_applications.py::test_list_users_forbidden_for_mentor`

---

## Matching and recommendations

Source: `backend/tests/test_api_matching.py`

### TC-133: A student gets mentors ranked by match score, each with the reasons

**User stories:** US-10

**API being tested:** `GET /api/v1/matching/recommendations`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"recommendations": [{"mentor_id": 1, "mentor_name": "Strong Match", "match_score": 90.0, "match_explanation": ["Career guidance fit", "Interest overlap matched", "Language match", "Strong experience level", "Availability and capacity open"]}, {"mentor_id": 2, "mentor_name": "Weak Match", "match_score": 10.0, "match_explanation": ["Career goal guidance not strongly aligned", "Language preference does not align", "Recent graduate perspective", "Availability and capacity open"]}]}`

**Result:** Success

pytest: `tests/test_api_matching.py::test_recommendations_ranked_with_score_and_reasons`

---

### TC-134: At most 5 mentors are recommended

**User stories:** US-10

**API being tested:** `GET /api/v1/matching/recommendations`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"recommendations": [{"mentor_id": 1, "mentor_name": "Mentor 0", "match_score": 10.0, "match_explanation": ["Career goal guidance not strongly aligned", "Language preference does not align", "Recent graduate perspective", "Availability and capacity open"]}, {"mentor_id": 2, "mentor_name": "Mentor 1", "match_score": 10.0, "match_explanation": ["Career goal guidance not strongly aligned", "Language preference does not align", "Recent graduate perspective", "Availability and capacity open"]}, {"mentor_id": 3, "mentor_name": "Mentor 2", "match_score": 10.0, "match_explanation": ["Career goal guidance not strongly aligned", "Language preference does not align", "Recent graduate perspective", "Availability and capacity open"]}, {"mentor_id": 4, "mentor_name": "Mentor 3", "match_score": 10.0, "match_explanation": ["Career goal guidance not strongly aligned", "Language preference does not align", "Recent graduate perspective", "Availability and capacity open"]}, {"mentor_id": 5, "mentor_name": "Mentor 4", "match_score": 10.0, "match_explanation": ["Career goal guidance not strongly aligned", "Language preference does not align", "Recent graduate perspective", "Availability and capacity open"]}]}`

**Result:** Success

pytest: `tests/test_api_matching.py::test_recommendations_limited_to_top_five`

---

### TC-135: Paused, full and suspended mentors are not recommended

**User stories:** US-08, US-10

**API being tested:** `GET /api/v1/matching/recommendations`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"recommendations": [{"mentor_id": 4, "mentor_name": "Available", "match_score": 10.0, "match_explanation": ["Career goal guidance not strongly aligned", "Language preference does not align", "Recent graduate perspective", "Availability and capacity open"]}]}`

**Result:** Success

pytest: `tests/test_api_matching.py::test_recommendations_skip_paused_full_and_suspended_mentors`

---

### TC-136: With no available mentors the list is empty

**User stories:** US-10

**API being tested:** `GET /api/v1/matching/recommendations`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 200
- JSON: `{"recommendations": []}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"recommendations": []}`

**Result:** Success

pytest: `tests/test_api_matching.py::test_recommendations_empty_when_no_mentors`

---

### TC-137: A student without a profile cannot get recommendations

**User stories:** US-04, US-10

**API being tested:** `GET /api/v1/matching/recommendations`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Student profile not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Student profile not found"}`

**Result:** Success

pytest: `tests/test_api_matching.py::test_recommendations_need_student_profile`

---

### TC-138: A mentor cannot ask for recommendations

**User stories:** US-10

**API being tested:** `GET /api/v1/matching/recommendations`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <mentor token>`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Student access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Student access required"}`

**Result:** Success

pytest: `tests/test_api_matching.py::test_recommendations_forbidden_for_mentor`

---

### TC-139: Recommendations cannot be fetched without logging in

**User stories:** US-10

**API being tested:** `GET /api/v1/matching/recommendations`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)

**Expected Output:**
- HTTP Status Code: 401

**Actual Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Not authenticated"}`

**Result:** Success

pytest: `tests/test_api_matching.py::test_recommendations_require_login`

---

### TC-140: A student sends a request to a mentor straight from the recommendations

**User stories:** US-10, US-12

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 1, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)"}`

**Expected Output:**
- HTTP Status Code: 201

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Available mentor not found"}`

**Result:** Fail

> **Defect found:** Recommendations return mentor_id = mentor PROFILE id, but POST /requests expects the mentor USER id, so requesting a recommended mentor fails (404).

pytest: `tests/test_api_matching.py::test_student_can_request_a_recommended_mentor`

---

### TC-141: Matching goal words in the mentor's guidance types add 35 points

**User stories:** US-10

**Function being tested:** `app.services.matching.calculate_match` (unit test, no HTTP call)

**Inputs / expected output:** see `tests/test_api_matching.py::test_score_rewards_guidance_fit`

**Result:** Success

pytest: `tests/test_api_matching.py::test_score_rewards_guidance_fit`

---

### TC-142: Interest overlap adds up to 30 points in proportion to shared interests

**User stories:** US-10

**Function being tested:** `app.services.matching.calculate_match` (unit test, no HTTP call)

**Inputs / expected output:** see `tests/test_api_matching.py::test_score_interest_overlap_is_proportional`

**Result:** Success

pytest: `tests/test_api_matching.py::test_score_interest_overlap_is_proportional`

---

### TC-143: A shared language adds 10 points; a different one is explained

**User stories:** US-10

**Function being tested:** `app.services.matching.calculate_match` (unit test, no HTTP call)

**Inputs / expected output:** see `tests/test_api_matching.py::test_score_language_match_and_mismatch`

**Result:** Success

pytest: `tests/test_api_matching.py::test_score_language_match_and_mismatch`

---

### TC-144: Senior mentors score higher than experienced, who score higher than recent graduates [Senior-10]

**User stories:** US-10

**Function being tested:** `app.services.matching.calculate_match` (unit test, no HTTP call)

**Inputs / expected output:** see `tests/test_api_matching.py::test_score_experience_level[Senior-10]`

**Result:** Success

pytest: `tests/test_api_matching.py::test_score_experience_level[Senior-10]`

---

### TC-145: Senior mentors score higher than experienced, who score higher than recent graduates [Experienced-7]

**User stories:** US-10

**Function being tested:** `app.services.matching.calculate_match` (unit test, no HTTP call)

**Inputs / expected output:** see `tests/test_api_matching.py::test_score_experience_level[Experienced-7]`

**Result:** Success

pytest: `tests/test_api_matching.py::test_score_experience_level[Experienced-7]`

---

### TC-146: Senior mentors score higher than experienced, who score higher than recent graduates [Recent Graduate-5]

**User stories:** US-10

**Function being tested:** `app.services.matching.calculate_match` (unit test, no HTTP call)

**Inputs / expected output:** see `tests/test_api_matching.py::test_score_experience_level[Recent Graduate-5]`

**Result:** Success

pytest: `tests/test_api_matching.py::test_score_experience_level[Recent Graduate-5]`

---

### TC-147: A mentor at capacity loses the availability points

**User stories:** US-08, US-10

**Function being tested:** `app.services.matching.calculate_match` (unit test, no HTTP call)

**Inputs / expected output:** see `tests/test_api_matching.py::test_score_full_mentor_loses_capacity_points`

**Result:** Success

pytest: `tests/test_api_matching.py::test_score_full_mentor_loses_capacity_points`

---

### TC-148: The match score is capped at 100

**User stories:** US-10

**Function being tested:** `app.services.matching.calculate_match` (unit test, no HTTP call)

**Inputs / expected output:** see `tests/test_api_matching.py::test_score_never_exceeds_100`

**Result:** Success

pytest: `tests/test_api_matching.py::test_score_never_exceeds_100`

---

## Mentoring requests

Source: `backend/tests/test_api_requests.py`

### TC-149: A student sends a mentoring request with a personal message

**User stories:** US-12

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 2, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)", "career_question_id": 1}`

**Expected Output:**
- HTTP Status Code: 201
- JSON containing: `{"student_id": 1, "mentor_id": 2, "status": "pending", "career_question_id": 1}`

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 1, "student_id": 1, "mentor_id": 2, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)", "career_question_id": 1, "decline_reason": null, "status": "pending", "created_at": "2026-11-17T17:07:59.133865+00:00", "decision_at": null, "withdrawn_at": null}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_student_sends_request_and_mentor_is_notified`

---

### TC-150: Personal messages of exactly 100 and 1,000 characters are accepted [exactly-100]

**User stories:** US-12

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 2, "personal_message": "<100 characters: 'mmmmmmmmmmmm'...>"}`

**Expected Output:**
- HTTP Status Code: 201

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 1, "student_id": 1, "mentor_id": 2, "personal_message": "<100 characters: 'mmmmmmmmmmmm'...>", "career_question_id": null, "decline_reason": null, "status": "pending", "created_at": "2026-11-17T17:07:59.336213+00:00", "decision_at": null, "withdrawn_at": null}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_request_message_length_boundaries_accepted[exactly-100]`

---

### TC-151: Personal messages of exactly 100 and 1,000 characters are accepted [exactly-1000]

**User stories:** US-12

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 2, "personal_message": "<1000 characters: 'mmmmmmmmmmmm'...>"}`

**Expected Output:**
- HTTP Status Code: 201

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 1, "student_id": 1, "mentor_id": 2, "personal_message": "<1000 characters: 'mmmmmmmmmmmm'...>", "career_question_id": null, "decline_reason": null, "status": "pending", "created_at": "2026-11-17T17:07:59.531918+00:00", "decision_at": null, "withdrawn_at": null}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_request_message_length_boundaries_accepted[exactly-1000]`

---

### TC-152: Messages under 100 or over 1,000 characters, or padded with spaces, are rejected [99-chars]

**User stories:** US-12

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 2, "personal_message": "<99 characters: 'mmmmmmmmmmmm'...>"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_short", "loc": ["body", "personal_message"], "msg": "String should have at least 100 characters", "input": "<99 characters: 'mmmmmmmmmmmm'...>", "ctx": {"min_length": 100}}]}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_request_message_length_boundaries_rejected[99-chars]`

---

### TC-153: Messages under 100 or over 1,000 characters, or padded with spaces, are rejected [1001-chars]

**User stories:** US-12

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 2, "personal_message": "<1001 characters: 'mmmmmmmmmmmm'...>"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_long", "loc": ["body", "personal_message"], "msg": "String should have at most 1000 characters", "input": "<1001 characters: 'mmmmmmmmmmmm'...>", "ctx": {"max_length": 1000}}]}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_request_message_length_boundaries_rejected[1001-chars]`

---

### TC-154: Messages under 100 or over 1,000 characters, or padded with spaces, are rejected [100-chars-mostly-spaces]

**User stories:** US-12

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 2, "personal_message": "<100 characters: 'mmmmmmmmmmmm'...>"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "value_error", "loc": ["body", "personal_message"], "msg": "Value error, Personal message must contain at least 100 non-whitespace characters", "input": "<100 characters: 'mmmmmmmmmmmm'...>", "ctx": {"error": {}}}]}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_request_message_length_boundaries_rejected[100-chars-mostly-spaces]`

---

### TC-155: A student cannot have more than 3 pending requests

**User stories:** US-12

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 6, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "At most three mentoring requests may be pending"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "At most three mentoring requests may be pending"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_fourth_pending_request_is_refused`

---

### TC-156: A second pending request to the same mentor is refused

**User stories:** US-12

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 2, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "A pending request or active relationship already exists"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "A pending request or active relationship already exists"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_duplicate_pending_request_is_refused`

---

### TC-157: A student cannot request a mentor they already have

**User stories:** US-12

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 2, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "A pending request or active relationship already exists"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "A pending request or active relationship already exists"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_request_to_current_mentor_is_refused`

---

### TC-158: A request to a mentor with no free slots is refused

**User stories:** US-08, US-12

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 1, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Mentor is at capacity"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Mentor is at capacity"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_request_to_mentor_at_capacity_is_refused`

---

### TC-159: A request to a paused mentor is refused

**User stories:** US-08, US-12

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 1, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Mentor is not accepting requests"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Mentor is not accepting requests"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_request_to_paused_mentor_is_refused`

---

### TC-160: A request to a mentor who is not yet approved is refused

**User stories:** US-03, US-12

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 1, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)"}`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Available mentor not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Available mentor not found"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_request_to_unverified_mentor_is_refused`

---

### TC-161: A request to a suspended mentor is refused

**User stories:** US-12, US-24

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 1, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)"}`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Available mentor not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Available mentor not found"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_request_to_suspended_mentor_is_refused`

---

### TC-162: Sending a request to a user who is not a mentor is refused

**User stories:** US-12

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 1, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)"}`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Available mentor not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Available mentor not found"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_request_to_a_student_id_is_refused`

---

### TC-163: A student cannot attach another student's career question

**User stories:** US-05, US-12

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 3, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)", "career_question_id": 1}`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Career question not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Career question not found"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_request_with_another_students_question_is_refused`

---

### TC-164: A mentor cannot send a mentoring request

**User stories:** US-12

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor B token>`
- JSON: `{"mentor_id": 1, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)"}`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Student access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Student access required"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_mentor_cannot_send_request`

---

### TC-165: After a decline the student may send a new request to the same mentor

**User stories:** US-12, US-13

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 2, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)"}`

**Expected Output:**
- HTTP Status Code: 201
- JSON containing: `{"status": "pending"}`

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 2, "student_id": 1, "mentor_id": 2, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)", "career_question_id": null, "decline_reason": null, "status": "pending", "created_at": "2026-11-17T17:08:02.679490+00:00", "decision_at": null, "withdrawn_at": null}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_student_can_request_again_after_decline`

---

### TC-166: A student sees only their own requests

**User stories:** US-14

**API being tested:** `GET /api/v1/requests`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "student_id": 1, "mentor_id": 3, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)", "career_question_id": null, "decline_reason": null, "status": "pending", "created_at": "2026-11-17T17:08:02.930205+00:00", "decision_at": null, "withdrawn_at": null}]}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_student_lists_only_own_requests`

---

### TC-167: A mentor sees incoming requests with the student's goal and question

**User stories:** US-05, US-13

**API being tested:** `GET /api/v1/requests`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <mentor token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "student_id": 1, "mentor_id": 2, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)", "career_question_id": 1, "decline_reason": null, "status": "pending", "created_at": "2026-11-17T17:08:03.217660+00:00", "decision_at": null, "withdrawn_at": null, "student": {"name": "Student 1", "career_goal": "Higher Studies", "current_situation": "Working professional", "career_question": "How should I prepare for data science interviews in my final term of the BS degree?"}}]}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_mentor_sees_incoming_requests_with_student_context`

---

### TC-168: An administrator cannot use the requests list

**User stories:** US-14

**API being tested:** `GET /api/v1/requests`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Student or mentor access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Student or mentor access required"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_admin_cannot_list_requests`

---

### TC-169: A request with no answer for 7 days is marked expired and both sides are told

**User stories:** US-13, US-14

**API being tested:** `GET /api/v1/requests`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "student_id": 1, "mentor_id": 2, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)", "career_question_id": null, "decline_reason": null, "status": "expired", "created_at": "2026-11-10T17:07:03.519946+00:00", "decision_at": "2026-11-17T17:08:03.536940+00:00", "withdrawn_at": null}]}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_request_expires_after_seven_days`

---

### TC-170: A request that is 6 days old is still pending

**User stories:** US-13

**API being tested:** `GET /api/v1/requests`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "student_id": 1, "mentor_id": 2, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)", "career_question_id": null, "decline_reason": null, "status": "pending", "created_at": "2026-11-11T17:08:03.757032+00:00", "decision_at": null, "withdrawn_at": null}]}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_request_six_days_old_stays_pending`

---

### TC-171: Accepting a request starts a mentoring relationship and tells the student

**User stories:** US-13, US-14, US-15

**API being tested:** `POST /api/v1/requests/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"action": "accept"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"id": 1, "status": "accepted"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "accepted", "decision_at": "2026-11-17T17:08:03.977433+00:00"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_mentor_accepts_request_and_relationship_starts`

---

### TC-172: A mentor declines with an optional reason and the student is told

**User stories:** US-13

**API being tested:** `POST /api/v1/requests/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"action": "decline", "decline_reason": "My expertise is in research, not industry jobs."}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"status": "rejected"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "rejected", "decision_at": "2026-11-17T17:08:04.226357+00:00"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_mentor_declines_request_with_reason`

---

### TC-173: The decline reason is optional

**User stories:** US-13

**API being tested:** `POST /api/v1/requests/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"action": "decline"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"status": "rejected"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "rejected", "decision_at": "2026-11-17T17:08:04.474707+00:00"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_mentor_declines_without_reason`

---

### TC-174: A mentor cannot accept more mentees than their capacity

**User stories:** US-08, US-13

**API being tested:** `POST /api/v1/requests/2/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"action": "accept"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Mentor is at capacity"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Mentor is at capacity"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_accept_refused_when_mentor_is_full`

---

### TC-175: A paused mentor cannot accept requests

**User stories:** US-08, US-13

**API being tested:** `POST /api/v1/requests/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"action": "accept"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Mentor is unavailable"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Mentor is unavailable"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_accept_refused_when_mentor_paused`

---

### TC-176: A request older than 7 days can no longer be accepted

**User stories:** US-13

**API being tested:** `POST /api/v1/requests/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"action": "accept"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Request is expired"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Request is expired"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_decision_on_expired_request_is_refused`

---

### TC-177: A request that was already accepted cannot be decided again

**User stories:** US-13

**API being tested:** `POST /api/v1/requests/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"action": "decline"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Request is accepted"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Request is accepted"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_request_cannot_be_decided_twice`

---

### TC-178: A mentor cannot decide a request sent to someone else

**User stories:** US-13

**API being tested:** `POST /api/v1/requests/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor B token>`
- JSON: `{"action": "accept"}`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Request not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Request not found"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_other_mentor_cannot_decide`

---

### TC-179: A student cannot accept their own request

**User stories:** US-13

**API being tested:** `POST /api/v1/requests/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"action": "accept"}`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Mentor access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Mentor access required"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_student_cannot_decide`

---

### TC-180: Unknown actions, missing actions and over-long decline reasons are rejected [unknown-action]

**User stories:** US-13

**API being tested:** `POST /api/v1/requests/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"action": "maybe"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "literal_error", "loc": ["body", "action"], "msg": "Input should be 'accept' or 'decline'", "input": "maybe", "ctx": {"expected": "'accept' or 'decline'"}}]}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_decision_validates_body[unknown-action]`

---

### TC-181: Unknown actions, missing actions and over-long decline reasons are rejected [reason-1001-chars]

**User stories:** US-13

**API being tested:** `POST /api/v1/requests/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"action": "decline", "decline_reason": "<1001 characters: 'rrrrrrrrrrrr'...>"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_long", "loc": ["body", "decline_reason"], "msg": "String should have at most 1000 characters", "input": "<1001 characters: 'rrrrrrrrrrrr'...>", "ctx": {"max_length": 1000}}]}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_decision_validates_body[reason-1001-chars]`

---

### TC-182: Unknown actions, missing actions and over-long decline reasons are rejected [missing-action]

**User stories:** US-13

**API being tested:** `POST /api/v1/requests/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "missing", "loc": ["body", "action"], "msg": "Field required", "input": {}}]}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_decision_validates_body[missing-action]`

---

### TC-183: A student withdraws a pending request and the mentor is told

**User stories:** US-16

**API being tested:** `POST /api/v1/requests/1/withdraw`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"id": 1, "status": "withdrawn"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "withdrawn", "withdrawn_at": "2026-11-17T17:08:06.917184+00:00"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_student_withdraws_pending_request`

---

### TC-184: Withdrawing frees one of the 3 pending-request slots

**User stories:** US-12, US-16

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"mentor_id": 6, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)"}`

**Expected Output:**
- HTTP Status Code: 201

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 4, "student_id": 1, "mentor_id": 6, "personal_message": "I am preparing to graduate and would like guidance on moving... (127 characters)", "career_question_id": null, "decline_reason": null, "status": "pending", "created_at": "2026-11-17T17:08:07.497163+00:00", "decision_at": null, "withdrawn_at": null}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_withdraw_frees_a_request_slot`

---

### TC-185: An accepted request cannot be withdrawn

**User stories:** US-16

**API being tested:** `POST /api/v1/requests/1/withdraw`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Only pending requests can be withdrawn"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Only pending requests can be withdrawn"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_accepted_request_cannot_be_withdrawn`

---

### TC-186: A mentor cannot accept a request the student withdrew

**User stories:** US-13, US-16

**API being tested:** `POST /api/v1/requests/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"action": "accept"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Request is withdrawn"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Request is withdrawn"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_withdrawn_request_cannot_be_accepted`

---

### TC-187: A student cannot withdraw another student's request

**User stories:** US-16

**API being tested:** `POST /api/v1/requests/1/withdraw`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student B token>`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Request not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Request not found"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_student_cannot_withdraw_someone_elses_request`

---

### TC-188: A mentor cannot use withdraw

**User stories:** US-16

**API being tested:** `POST /api/v1/requests/1/withdraw`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Student access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Student access required"}`

**Result:** Success

pytest: `tests/test_api_requests.py::test_mentor_cannot_withdraw`

---

## Relationships, sessions, notes and messages

Source: `backend/tests/test_api_relationships.py`

### TC-189: Both sides see the active relationship with names and context

**User stories:** US-14, US-15

**API being tested:** `GET /api/v1/relationships`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <mentor token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "student_id": 1, "mentor_id": 2, "student_name": "Kiran", "mentor_name": "Lakshmi", "status": "active", "started_at": "2026-11-17T17:07:46.071929+00:00", "ended_at": null, "closure_reason": null, "last_activity_at": "2026-11-17T17:07:46.071931+00:00", "student_career_goal": "Job", "student_interests": ["Data Science"], "current_question": "How should I prepare for data science interviews in my final term of the BS degree?", "mentor_career_history": "5 years at TCS", "mentor_expertise": ["Data Science"]}]}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_student_and_mentor_both_see_relationship`

---

### TC-190: A mentor sees every mentee assigned to them

**User stories:** US-15

**API being tested:** `GET /api/v1/relationships`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <mentor token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 3, "student_id": 5, "mentor_id": 1, "student_name": "Student 4", "mentor_name": "Mentor 1", "status": "active", "started_at": "2026-11-17T17:07:46.498572+00:00", "ended_at": null, "closure_reason": null, "last_activity_at": "2026-11-17T17:07:46.498574+00:00", "student_career_goal": null, "student_interests": [], "current_question": null, "mentor_career_history": null, "mentor_expertise": []}, {"id": 2, "student_id": 4, "mentor_id": 1, "student_name": "Student 3", "mentor_name": "Mentor 1", "status": "active", "started_at": "2026-11-17T17:07:46.415892+00:00", "ended_at": null, "closure_reason": null, "last_activity_at": "2026-11-17T17:07:46.415895+00:00", "student_career_goal": null, "student_interests": [], "current_question": null, "mentor_career_history": null, "mentor_expertise": []}, {"id": 1, "student_id": 3, "mentor_id": 1, "student_name": "Student 2", "mentor_name": "Mentor 1", "status": "active", "started_at": "2026-11-17T17:07:46.332688+00:00", "ended_at": null, "closure_reason": null, "last_activity_at": "2026-11-17T17:07:46.332690+00:00", "student_career_goal": null, "student_interests": [], "current_question": null, "mentor_career_history": null, "mentor_expertise": []}]}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_mentor_sees_all_assigned_mentees`

---

### TC-191: A user who is not part of a relationship does not see it

**User stories:** US-15

**API being tested:** `GET /api/v1/relationships`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student B token>`

**Expected Output:**
- HTTP Status Code: 200
- JSON: `{"items": []}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": []}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_outsider_sees_no_relationships`

---

### TC-192: Relationships cannot be listed without logging in

**User stories:** US-14

**API being tested:** `GET /api/v1/relationships`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)

**Expected Output:**
- HTTP Status Code: 401

**Actual Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Not authenticated"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_relationships_require_login`

---

### TC-193: Either side closes the relationship with a reason [GOAL_ACHIEVED]

**User stories:** US-17

**API being tested:** `POST /api/v1/relationships/1/close`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"reason": "GOAL_ACHIEVED"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"id": 1, "status": "closed"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "closed", "ended_at": "2026-11-17T17:07:47.088503+00:00"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_close_relationship_with_reason[GOAL_ACHIEVED]`

---

### TC-194: Either side closes the relationship with a reason [NO_LONGER_NEEDED]

**User stories:** US-17

**API being tested:** `POST /api/v1/relationships/1/close`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"reason": "NO_LONGER_NEEDED"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"id": 1, "status": "closed"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "closed", "ended_at": "2026-11-17T17:07:47.371218+00:00"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_close_relationship_with_reason[NO_LONGER_NEEDED]`

---

### TC-195: Either side closes the relationship with a reason [NOT_A_GOOD_FIT]

**User stories:** US-17

**API being tested:** `POST /api/v1/relationships/1/close`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"reason": "NOT_A_GOOD_FIT"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"id": 1, "status": "closed"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "closed", "ended_at": "2026-11-17T17:07:47.620876+00:00"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_close_relationship_with_reason[NOT_A_GOOD_FIT]`

---

### TC-196: A mentor can close the relationship too

**User stories:** US-17

**API being tested:** `POST /api/v1/relationships/1/close`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"reason": "GOAL_ACHIEVED"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"status": "closed"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "closed", "ended_at": "2026-11-17T17:07:47.869430+00:00"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_mentor_can_close_relationship`

---

### TC-197: Closing a relationship frees the mentor's slot at once

**User stories:** US-17, US-08

**API being tested:** `POST /api/v1/requests`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student B token>`
- JSON: `{"mentor_id": 2, "personal_message": "<120 characters: 'nnnnnnnnnnnn'...>"}`

**Expected Output:**
- HTTP Status Code: 201

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 2, "student_id": 4, "mentor_id": 2, "personal_message": "<120 characters: 'nnnnnnnnnnnn'...>", "career_question_id": null, "decline_reason": null, "status": "pending", "created_at": "2026-11-17T17:07:48.185964+00:00", "decision_at": null, "withdrawn_at": null}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_closing_frees_mentor_slot_immediately`

---

### TC-198: Closing with reason OTHER needs an explanation

**User stories:** US-17

**API being tested:** `POST /api/v1/relationships/1/close`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"reason": "OTHER", "explanation": "   "}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: `{"detail": "An explanation is required for OTHER"}`

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": "An explanation is required for OTHER"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_close_with_other_needs_explanation`

---

### TC-199: Closing with reason OTHER and an explanation works

**User stories:** US-17

**API being tested:** `POST /api/v1/relationships/1/close`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"reason": "OTHER", "explanation": "I moved abroad for my master's degree."}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"status": "closed"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "closed", "ended_at": "2026-11-17T17:07:48.670333+00:00"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_close_with_other_and_explanation`

---

### TC-200: An unknown closure reason is rejected

**User stories:** US-17

**API being tested:** `POST /api/v1/relationships/1/close`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"reason": "BORED"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "literal_error", "loc": ["body", "reason"], "msg": "Input should be 'GOAL_ACHIEVED', 'NO_LONGER_NEEDED', 'NOT_A_GOOD_FIT' or 'OTHER'", "input": "BORED", "ctx": {"expected": "'GOAL_ACHIEVED', 'NO_LONGER_NEEDED', 'NOT_A_GOOD_FIT' or 'OTHER'"}}]}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_close_rejects_unknown_reason`

---

### TC-201: A closed relationship cannot be closed again

**User stories:** US-17

**API being tested:** `POST /api/v1/relationships/1/close`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"reason": "GOAL_ACHIEVED"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Relationship is not active"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Relationship is not active"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_close_twice_is_refused`

---

### TC-202: Someone outside the relationship cannot close it

**User stories:** US-17

**API being tested:** `POST /api/v1/relationships/1/close`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student B token>`
- JSON: `{"reason": "GOAL_ACHIEVED"}`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Relationship not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Relationship not found"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_outsider_cannot_close`

---

### TC-203: A session proposed in IST is stored in UTC and the other side is told

**User stories:** US-18

**API being tested:** `POST /api/v1/relationships/1/sessions`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"scheduled_for": "2026-12-05T19:30:00", "timezone": "Asia/Kolkata", "meeting_link": "https://meet.google.com/abc-defg-hij"}`

**Expected Output:**
- HTTP Status Code: 201
- JSON containing: `{"scheduled_for": "2026-12-05T14:00:00+00:00", "proposer_timezone": "Asia/Kolkata", "status": "proposed", "meeting_link": "https://meet.google.com/abc-defg-hij"}`

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 1, "scheduled_for": "2026-12-05T14:00:00+00:00", "proposer_timezone": "Asia/Kolkata", "status": "proposed", "meeting_link": "https://meet.google.com/abc-defg-hij"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_propose_session_in_local_time_zone`

---

### TC-204: A time with an explicit UTC offset is converted to UTC

**User stories:** US-18

**API being tested:** `POST /api/v1/relationships/1/sessions`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"scheduled_for": "2026-12-05T09:00:00-05:00", "timezone": "America/New_York"}`

**Expected Output:**
- HTTP Status Code: 201
- JSON containing: `{"scheduled_for": "2026-12-05T14:00:00+00:00"}`

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 1, "scheduled_for": "2026-12-05T14:00:00+00:00", "proposer_timezone": "America/New_York", "status": "proposed", "meeting_link": null}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_propose_session_with_explicit_offset`

---

### TC-205: Unknown zones and times that do not exist or happen twice (DST) are rejected [unknown-zone]

**User stories:** US-18

**API being tested:** `POST /api/v1/relationships/1/sessions`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"scheduled_for": "2026-12-05T19:30:00", "timezone": "Mars/Olympus"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: `{"detail": "Unknown timezone"}`

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": "Unknown timezone"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_propose_session_rejects_bad_local_times[unknown-zone]`

---

### TC-206: Unknown zones and times that do not exist or happen twice (DST) are rejected [skipped-by-dst]

**User stories:** US-18

**API being tested:** `POST /api/v1/relationships/1/sessions`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"scheduled_for": "2026-03-08T02:30:00", "timezone": "America/New_York"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: `{"detail": "Local time does not exist in this timezone"}`

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": "Local time does not exist in this timezone"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_propose_session_rejects_bad_local_times[skipped-by-dst]`

---

### TC-207: Unknown zones and times that do not exist or happen twice (DST) are rejected [repeated-by-dst]

**User stories:** US-18

**API being tested:** `POST /api/v1/relationships/1/sessions`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"scheduled_for": "2026-11-01T01:30:00", "timezone": "America/New_York"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: `{"detail": "Ambiguous local time; include an explicit UTC offset"}`

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": "Ambiguous local time; include an explicit UTC offset"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_propose_session_rejects_bad_local_times[repeated-by-dst]`

---

### TC-208: A proposal without a time or time zone is rejected

**User stories:** US-18

**API being tested:** `POST /api/v1/relationships/1/sessions`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"timezone": "UTC"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "missing", "loc": ["body", "scheduled_for"], "msg": "Field required", "input": {"timezone": "UTC"}}]}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_propose_session_needs_time_and_zone`

---

### TC-209: Sessions cannot be proposed after the relationship is closed

**User stories:** US-18

**API being tested:** `POST /api/v1/relationships/1/sessions`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"scheduled_for": "2026-12-05T10:00:00", "timezone": "UTC"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Relationship is not active"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Relationship is not active"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_propose_session_on_closed_relationship`

---

### TC-210: Someone outside the relationship cannot propose a session

**User stories:** US-18

**API being tested:** `POST /api/v1/relationships/1/sessions`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student B token>`
- JSON: `{"scheduled_for": "2026-12-05T10:00:00", "timezone": "UTC"}`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Relationship not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Relationship not found"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_outsider_cannot_propose_session`

---

### TC-211: Both sides list the sessions, latest first

**User stories:** US-18

**API being tested:** `GET /api/v1/relationships/1/sessions`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <mentor token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 2, "scheduled_for": "2026-11-26T17:07:21.393938+00:00", "proposer_id": 2, "proposer_timezone": "UTC", "status": "proposed", "meeting_link": null}, {"id": 1, "scheduled_for": "2026-11-19T17:07:21.393938+00:00", "proposer_id": 1, "proposer_timezone": "UTC", "status": "proposed", "meeting_link": null}]}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_list_sessions_latest_first`

---

### TC-212: Someone outside the relationship cannot list its sessions

**User stories:** US-18

**API being tested:** `GET /api/v1/relationships/1/sessions`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Relationship not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Relationship not found"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_outsider_cannot_list_sessions`

---

### TC-213: The other participant confirms a proposal or marks it not available [confirm-confirmed]

**User stories:** US-18

**API being tested:** `POST /api/v1/sessions/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"action": "confirm"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"id": 1, "status": "confirmed"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "confirmed", "scheduled_for": "2026-11-19T17:07:21.393938+00:00"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_other_side_confirms_or_marks_unavailable[confirm-confirmed]`

---

### TC-214: The other participant confirms a proposal or marks it not available [unavailable-unavailable]

**User stories:** US-18

**API being tested:** `POST /api/v1/sessions/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"action": "unavailable"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"id": 1, "status": "unavailable"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "unavailable", "scheduled_for": "2026-11-19T17:07:21.393938+00:00"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_other_side_confirms_or_marks_unavailable[unavailable-unavailable]`

---

### TC-215: The person who proposed cannot confirm their own proposal

**User stories:** US-18

**API being tested:** `POST /api/v1/sessions/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"action": "confirm"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Only the other participant may decide a proposal"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Only the other participant may decide a proposal"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_proposer_cannot_confirm_own_proposal`

---

### TC-216: The proposer can cancel a session

**User stories:** US-18

**API being tested:** `POST /api/v1/sessions/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"action": "cancel"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"status": "cancelled"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "cancelled", "scheduled_for": "2026-11-19T17:07:21.393938+00:00"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_proposer_cancels_session`

---

### TC-217: Only the proposer can cancel

**User stories:** US-18

**API being tested:** `POST /api/v1/sessions/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"action": "cancel"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Only the proposer may cancel this session"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Only the proposer may cancel this session"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_other_side_cannot_cancel`

---

### TC-218: A confirmed session in the past can be marked completed

**User stories:** US-18, US-20

**API being tested:** `POST /api/v1/sessions/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"action": "complete"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"status": "completed"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "completed", "scheduled_for": "2026-11-17T15:07:21.393938+00:00"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_complete_past_confirmed_session`

---

### TC-219: A session that has not happened yet cannot be completed

**User stories:** US-18

**API being tested:** `POST /api/v1/sessions/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"action": "complete"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Only past confirmed sessions can be completed"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Only past confirmed sessions can be completed"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_future_session_cannot_be_completed`

---

### TC-220: A session that was never confirmed cannot be completed

**User stories:** US-18

**API being tested:** `POST /api/v1/sessions/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"action": "complete"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Only past confirmed sessions can be completed"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Only past confirmed sessions can be completed"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_unconfirmed_session_cannot_be_completed`

---

### TC-221: Unknown actions are rejected and unknown sessions return 404

**User stories:** US-18

**Step 1: API being tested:** `POST /api/v1/sessions/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"action": "reschedule"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "literal_error", "loc": ["body", "action"], "msg": "Input should be 'confirm', 'unavailable', 'cancel' or 'complete'", "input": "reschedule", "ctx": {"expected": "'confirm', 'unavailable', 'cancel' or 'complete'"}}]}`

**Step 2: API being tested:** `POST /api/v1/sessions/9999/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"action": "confirm"}`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Session not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Session not found"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_session_decision_validation_and_unknown_session`

---

### TC-222: Session decisions stop once the relationship is closed

**User stories:** US-17, US-18

**API being tested:** `POST /api/v1/sessions/1/decision`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"action": "confirm"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Relationship is not active"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Relationship is not active"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_session_decision_after_relationship_closed`

---

### TC-223: After a session either side records notes and action items with a due date

**User stories:** US-20

**API being tested:** `POST /api/v1/sessions/1/notes`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"notes": "Discussed portfolio projects and the resume.", "action_items": "Build one end-to-end ML project", "due_at": "2026-12-15T12:00:00+00:00"}`

**Expected Output:**
- HTTP Status Code: 201
- JSON containing: `{"notes": "Discussed portfolio projects and the resume.", "action_items": "Build one end-to-end ML project", "due_at": "2026-12-15T12:00:00+00:00", "submitted_late": false}`

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 1, "notes": "Discussed portfolio projects and the resume.", "action_items": "Build one end-to-end ML project", "due_at": "2026-12-15T12:00:00+00:00", "submitted_late": false, "created_at": "2026-11-17T17:07:54.881869+00:00"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_add_notes_and_action_items_after_session`

---

### TC-224: Notes added more than 48 hours after the session are flagged as late

**User stories:** US-20

**API being tested:** `POST /api/v1/sessions/1/notes`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"notes": "Late summary of our session."}`

**Expected Output:**
- HTTP Status Code: 201
- JSON containing: `{"submitted_late": true}`

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 1, "notes": "Late summary of our session.", "action_items": null, "due_at": null, "submitted_late": true, "created_at": "2026-11-17T17:07:55.145245+00:00"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_notes_after_48_hours_are_flagged_late`

---

### TC-225: Notes cannot be added before the session has happened

**User stories:** US-20

**API being tested:** `POST /api/v1/sessions/1/notes`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"notes": "Too early."}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Notes can be added after the session"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Notes can be added after the session"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_notes_before_session_are_refused`

---

### TC-226: Empty or over-long notes are rejected [empty]

**User stories:** US-20

**API being tested:** `POST /api/v1/sessions/1/notes`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"notes": ""}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_short", "loc": ["body", "notes"], "msg": "String should have at least 1 character", "input": "", "ctx": {"min_length": 1}}]}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_notes_validation[empty]`

---

### TC-227: Empty or over-long notes are rejected [notes-10001]

**User stories:** US-20

**API being tested:** `POST /api/v1/sessions/1/notes`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"notes": "<10001 characters: 'nnnnnnnnnnnn'...>"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_long", "loc": ["body", "notes"], "msg": "String should have at most 10000 characters", "input": "<10001 characters: 'nnnnnnnnnnnn'...>", "ctx": {"max_length": 10000}}]}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_notes_validation[notes-10001]`

---

### TC-228: Empty or over-long notes are rejected [actions-5001]

**User stories:** US-20

**API being tested:** `POST /api/v1/sessions/1/notes`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"notes": "ok", "action_items": "<5001 characters: 'aaaaaaaaaaaa'...>"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_long", "loc": ["body", "action_items"], "msg": "String should have at most 5000 characters", "input": "<5001 characters: 'aaaaaaaaaaaa'...>", "ctx": {"max_length": 5000}}]}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_notes_validation[actions-5001]`

---

### TC-229: Both participants read the notes; outsiders and admins cannot

**User stories:** US-20

**Step 1: API being tested:** `GET /api/v1/sessions/1/notes`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "author_id": 2, "notes": "Mentor notes.", "action_items": null, "due_at": null, "submitted_late": false, "created_at": "2026-11-17T17:07:56.383941+00:00"}]}`

**Step 2: API being tested:** `GET /api/v1/sessions/1/notes`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Relationship not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Relationship not found"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_list_notes_for_participants_only`

---

### TC-230: A participant sends a message and the other side gets a notification without the text

**User stories:** US-19

**API being tested:** `POST /api/v1/relationships/1/messages`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"content": "Thank you for accepting. Could we talk about MS applications?"}`

**Expected Output:**
- HTTP Status Code: 201

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 1, "created_at": "2026-11-17T17:07:56.635813+00:00"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_send_message_in_active_relationship`

---

### TC-231: A message of exactly 2,000 characters is accepted

**User stories:** US-19

**API being tested:** `POST /api/v1/relationships/1/messages`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"content": "<2000 characters: 'mmmmmmmmmmmm'...>"}`

**Expected Output:**
- HTTP Status Code: 201

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 1, "created_at": "2026-11-17T17:07:56.885261+00:00"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_message_of_2000_characters_accepted`

---

### TC-232: Messages over 2,000 characters, empty or blank are rejected [2001-chars]

**User stories:** US-19

**API being tested:** `POST /api/v1/relationships/1/messages`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"content": "<2001 characters: 'mmmmmmmmmmmm'...>"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_long", "loc": ["body", "content"], "msg": "String should have at most 2000 characters", "input": "<2001 characters: 'mmmmmmmmmmmm'...>", "ctx": {"max_length": 2000}}]}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_message_validation[2001-chars]`

---

### TC-233: Messages over 2,000 characters, empty or blank are rejected [empty]

**User stories:** US-19

**API being tested:** `POST /api/v1/relationships/1/messages`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"content": ""}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_short", "loc": ["body", "content"], "msg": "String should have at least 1 character", "input": "", "ctx": {"min_length": 1}}]}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_message_validation[empty]`

---

### TC-234: Messages over 2,000 characters, empty or blank are rejected [only-spaces]

**User stories:** US-19

**API being tested:** `POST /api/v1/relationships/1/messages`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"content": "    "}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "value_error", "loc": ["body", "content"], "msg": "Value error, Message cannot be blank", "input": "    ", "ctx": {"error": {}}}]}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_message_validation[only-spaces]`

---

### TC-235: Messages cannot be sent once the relationship is closed

**User stories:** US-17, US-19

**API being tested:** `POST /api/v1/relationships/1/messages`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"content": "Hello again"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Relationship is not active"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Relationship is not active"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_message_after_close_is_refused`

---

### TC-236: Someone outside the relationship cannot send a message in it

**User stories:** US-19

**API being tested:** `POST /api/v1/relationships/1/messages`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student B token>`
- JSON: `{"content": "Hi"}`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Relationship not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Relationship not found"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_outsider_cannot_send_message`

---

### TC-237: Reading the conversation marks the reader's incoming messages as read

**User stories:** US-19

**API being tested:** `GET /api/v1/relationships/1/messages`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <mentor token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "sender_id": 1, "recipient_id": 2, "content": "First", "is_read": true, "created_at": "2026-11-17T17:07:58.374066+00:00"}, {"id": 2, "sender_id": 2, "recipient_id": 1, "content": "Reply", "is_read": false, "created_at": "2026-11-17T17:07:58.392449+00:00"}]}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_read_messages_marks_them_read`

---

### TC-238: An administrator cannot read private messages

**User stories:** US-19, US-21

**API being tested:** `GET /api/v1/relationships/1/messages`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Relationship not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Relationship not found"}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_admin_cannot_read_messages`

---

### TC-239: Message history stays readable after the relationship is closed

**User stories:** US-17, US-19

**API being tested:** `GET /api/v1/relationships/1/messages`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "sender_id": 1, "recipient_id": 2, "content": "Before closing", "is_read": false, "created_at": "2026-11-17T17:07:58.898503+00:00"}]}`

**Result:** Success

pytest: `tests/test_api_relationships.py::test_message_history_still_readable_after_close`

---

## Reports, moderation, alerts, analytics and notifications

Source: `backend/tests/test_api_moderation_insights.py`

### TC-240: A student reports a mentor; every active admin gets a notification

**User stories:** US-23

**API being tested:** `POST /api/v1/reports`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"target_user_id": 3, "category": "HARASSMENT", "description": "Sent repeated promotional messages about a paid course after I declined."}`

**Expected Output:**
- HTTP Status Code: 201
- JSON containing: `{"status": "open"}`

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 1, "status": "open", "created_at": "2026-11-17T17:07:37.609560+00:00"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_student_reports_mentor_and_admins_are_told`

---

### TC-241: A mentor can report a student

**User stories:** US-23

**API being tested:** `POST /api/v1/reports`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"target_user_id": 1, "category": "INAPPROPRIATE_BEHAVIOUR", "description": "Sent repeated promotional messages about a paid course after I declined."}`

**Expected Output:**
- HTTP Status Code: 201
- JSON containing: `{"status": "open"}`

**Actual Output:**
- HTTP Status Code: 201
- JSON: `{"id": 1, "status": "open", "created_at": "2026-11-17T17:07:37.823437+00:00"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_mentor_can_report_student`

---

### TC-242: Unknown categories and descriptions under 20 or over 4,000 characters are rejected [unknown-category]

**User stories:** US-23

**API being tested:** `POST /api/v1/reports`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"target_user_id": 2, "category": "RUDE", "description": "Sent repeated promotional messages about a paid course after I declined."}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "literal_error", "loc": ["body", "category"], "msg": "Input should be 'HARASSMENT', 'INAPPROPRIATE_BEHAVIOUR', 'SP... (95 characters)", "input": "RUDE", "ctx": {"expected": "'HARASSMENT', 'INAPPROPRIATE_BEHAVIOUR', 'SPAM', 'MISREPRESENTATION' or 'OTHER'"}}]}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_report_validation[unknown-category]`

---

### TC-243: Unknown categories and descriptions under 20 or over 4,000 characters are rejected [description-9-chars]

**User stories:** US-23

**API being tested:** `POST /api/v1/reports`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"target_user_id": 2, "category": "SPAM", "description": "too short"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_short", "loc": ["body", "description"], "msg": "String should have at least 20 characters", "input": "too short", "ctx": {"min_length": 20}}]}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_report_validation[description-9-chars]`

---

### TC-244: Unknown categories and descriptions under 20 or over 4,000 characters are rejected [description-4001-chars]

**User stories:** US-23

**API being tested:** `POST /api/v1/reports`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"target_user_id": 2, "category": "SPAM", "description": "<4001 characters: 'xxxxxxxxxxxx'...>"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_long", "loc": ["body", "description"], "msg": "String should have at most 4000 characters", "input": "<4001 characters: 'xxxxxxxxxxxx'...>", "ctx": {"max_length": 4000}}]}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_report_validation[description-4001-chars]`

---

### TC-245: Unknown categories and descriptions under 20 or over 4,000 characters are rejected [description-mostly-spaces]

**User stories:** US-23

**API being tested:** `POST /api/v1/reports`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"target_user_id": 2, "category": "SPAM", "description": "               short"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "value_error", "loc": ["body", "description"], "msg": "Value error, Description must contain at least 20 non-whitespace characters", "input": "               short", "ctx": {"error": {}}}]}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_report_validation[description-mostly-spaces]`

---

### TC-246: Unknown categories and descriptions under 20 or over 4,000 characters are rejected [target-id-0]

**User stories:** US-23

**API being tested:** `POST /api/v1/reports`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"target_user_id": 0, "category": "SPAM", "description": "Sent repeated promotional messages about a paid course after I declined."}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "greater_than", "loc": ["body", "target_user_id"], "msg": "Input should be greater than 0", "input": 0, "ctx": {"gt": 0}}]}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_report_validation[target-id-0]`

---

### TC-247: A user cannot report themselves

**User stories:** US-23

**API being tested:** `POST /api/v1/reports`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"target_user_id": 1, "category": "SPAM", "description": "Sent repeated promotional messages about a paid course after I declined."}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: `{"detail": "You cannot report yourself"}`

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": "You cannot report yourself"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_cannot_report_yourself`

---

### TC-248: Reporting a user that does not exist returns 404

**User stories:** US-23

**API being tested:** `POST /api/v1/reports`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"target_user_id": 9999, "category": "SPAM", "description": "Sent repeated promotional messages about a paid course after I declined."}`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Reported user not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Reported user not found"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_cannot_report_unknown_user`

---

### TC-249: A second report while the first is still open is refused

**User stories:** US-23

**API being tested:** `POST /api/v1/reports`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"target_user_id": 2, "category": "HARASSMENT", "description": "Sent repeated promotional messages about a paid course after I declined."}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "An unresolved report for this user already exists"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "An unresolved report for this user already exists"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_duplicate_open_report_is_refused`

---

### TC-250: Administrators do not file reports themselves

**User stories:** US-23

**API being tested:** `POST /api/v1/reports`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"target_user_id": 1, "category": "SPAM", "description": "Sent repeated promotional messages about a paid course after I declined."}`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Only students and mentors may submit reports"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Only students and mentors may submit reports"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_admin_cannot_file_report`

---

### TC-251: An admin lists reports with category, description and status

**User stories:** US-24

**API being tested:** `GET /api/v1/admin/reports`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 1, "reporter_id": 1, "target_user_id": 2, "category": "spam", "description": "Sent repeated promotional messages about a paid course after I declined.", "status": "open", "admin_review_notes": null, "created_at": "2026-11-17T17:07:39.360670+00:00"}]}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_admin_lists_reports`

---

### TC-252: A student cannot list reports

**User stories:** US-24

**API being tested:** `GET /api/v1/admin/reports`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_student_cannot_list_reports`

---

### TC-253: An admin moves a report to under review, resolved or dismissed with notes, and it is audited [under_review]

**User stories:** US-24

**API being tested:** `POST /api/v1/admin/reports/1/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"status": "under_review", "admin_review_notes": "Checked message history with both users."}`

**Expected Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "under_review"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "under_review"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_admin_reviews_report[under_review]`

---

### TC-254: An admin moves a report to under review, resolved or dismissed with notes, and it is audited [resolved]

**User stories:** US-24

**API being tested:** `POST /api/v1/admin/reports/1/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"status": "resolved", "admin_review_notes": "Checked message history with both users."}`

**Expected Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "resolved"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "resolved"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_admin_reviews_report[resolved]`

---

### TC-255: An admin moves a report to under review, resolved or dismissed with notes, and it is audited [dismissed]

**User stories:** US-24

**API being tested:** `POST /api/v1/admin/reports/1/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"status": "dismissed", "admin_review_notes": "Checked message history with both users."}`

**Expected Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "dismissed"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "status": "dismissed"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_admin_reviews_report[dismissed]`

---

### TC-256: A resolved report is final

**User stories:** US-24

**API being tested:** `POST /api/v1/admin/reports/1/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"status": "dismissed", "admin_review_notes": "Second look."}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Report has already been resolved"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Report has already been resolved"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_resolved_report_cannot_be_reviewed_again`

---

### TC-257: Unknown statuses and notes under 5 characters are rejected [unknown-status]

**User stories:** US-24

**API being tested:** `POST /api/v1/admin/reports/1/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"status": "closed", "admin_review_notes": "Valid notes"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "literal_error", "loc": ["body", "status"], "msg": "Input should be 'under_review', 'resolved' or 'dismissed'", "input": "closed", "ctx": {"expected": "'under_review', 'resolved' or 'dismissed'"}}]}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_report_review_validation[unknown-status]`

---

### TC-258: Unknown statuses and notes under 5 characters are rejected [notes-2-chars]

**User stories:** US-24

**API being tested:** `POST /api/v1/admin/reports/1/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"status": "resolved", "admin_review_notes": "ok"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "string_too_short", "loc": ["body", "admin_review_notes"], "msg": "String should have at least 5 characters", "input": "ok", "ctx": {"min_length": 5}}]}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_report_review_validation[notes-2-chars]`

---

### TC-259: Reviewing a report that does not exist returns 404

**User stories:** US-24

**API being tested:** `POST /api/v1/admin/reports/9999/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"status": "resolved", "admin_review_notes": "Nothing here."}`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Report not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Report not found"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_review_unknown_report`

---

### TC-260: A mentor cannot review reports

**User stories:** US-24

**API being tested:** `POST /api/v1/admin/reports/1/review`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`
- JSON: `{"status": "dismissed", "admin_review_notes": "Not a problem."}`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_mentor_cannot_review_report`

---

### TC-261: Suspending a mentor blocks the account, pauses their relationships and records the reason

**User stories:** US-24

**API being tested:** `POST /api/v1/admin/users/2/suspend`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"reason": "Confirmed harassment after reviewing the report."}`

**Expected Output:**
- HTTP Status Code: 200
- JSON: `{"id": 2, "account_status": "suspended", "suspended_relationships": 1}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 2, "account_status": "suspended", "suspended_relationships": 1}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_suspend_user_pauses_relationships_and_is_audited`

---

### TC-262: No messages can be sent in a relationship paused by suspension

**User stories:** US-19, US-24

**API being tested:** `POST /api/v1/relationships/1/messages`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"content": "Are you there?"}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Relationship is not active"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Relationship is not active"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_message_to_suspended_user_is_refused`

---

### TC-263: Reactivating restores the account and resumes its relationships

**User stories:** US-24

**API being tested:** `POST /api/v1/admin/users/2/reactivate`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"reason": "Appeal accepted after review of evidence."}`

**Expected Output:**
- HTTP Status Code: 200
- JSON: `{"id": 2, "account_status": "active"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 2, "account_status": "active"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_reactivate_restores_account_and_relationship`

---

### TC-264: A suspended mentor who was still unverified goes back to pending verification

**User stories:** US-03, US-24

**API being tested:** `POST /api/v1/admin/users/1/reactivate`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"reason": "Suspended by mistake, restoring."}`

**Expected Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "account_status": "pending_verification"}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "account_status": "pending_verification"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_reactivate_returns_pending_mentor_to_pending`

---

### TC-265: A relationship resumes only when neither side is suspended

**User stories:** US-24

**API being tested:** `POST /api/v1/admin/users/2/reactivate`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"reason": "Mentor appeal accepted."}`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 2, "account_status": "active"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_relationship_stays_paused_while_other_side_suspended`

---

### TC-266: Admins cannot suspend themselves, suspend twice, or suspend unknown users [self-Administrators cannot suspend their own account]

**User stories:** US-24

**API being tested:** `POST /api/v1/admin/users/1/suspend`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"reason": "Testing suspension rules."}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Administrators cannot suspend their own account"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "Administrators cannot suspend their own account"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_suspend_refusals[self-Administrators cannot suspend their own account]`

---

### TC-267: Admins cannot suspend themselves, suspend twice, or suspend unknown users [twice-User is already suspended]

**User stories:** US-24

**API being tested:** `POST /api/v1/admin/users/2/suspend`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"reason": "Testing suspension rules."}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "User is already suspended"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "User is already suspended"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_suspend_refusals[twice-User is already suspended]`

---

### TC-268: Admins cannot suspend themselves, suspend twice, or suspend unknown users [unknown-User not found]

**User stories:** US-24

**API being tested:** `POST /api/v1/admin/users/9999/suspend`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"reason": "Testing suspension rules."}`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "User not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "User not found"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_suspend_refusals[unknown-User not found]`

---

### TC-269: A suspension reason under 10 real characters is rejected

**User stories:** US-24

**API being tested:** `POST /api/v1/admin/users/1/suspend`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"reason": "   spam    "}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: validation error (`detail` lists the invalid field)

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": [{"type": "value_error", "loc": ["body", "reason"], "msg": "Value error, Reason must contain at least 10 non-whitespace characters", "input": "   spam    ", "ctx": {"error": {}}}]}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_suspend_requires_reason`

---

### TC-270: Reactivating a user who is not suspended is refused

**User stories:** US-24

**API being tested:** `POST /api/v1/admin/users/1/reactivate`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <admin token>`
- JSON: `{"reason": "Nothing to reactivate."}`

**Expected Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "User is not suspended"}`

**Actual Output:**
- HTTP Status Code: 409
- JSON: `{"detail": "User is not suspended"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_reactivate_active_user_is_refused`

---

### TC-271: A student cannot suspend another user

**User stories:** US-24

**API being tested:** `POST /api/v1/admin/users/1/suspend`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`
- JSON: `{"reason": "I do not like them."}`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_student_cannot_suspend`

---

### TC-272: Admins see requests pending over 5 days and relationships idle for 30 days

**User stories:** US-22

**API being tested:** `GET /api/v1/admin/alerts`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"stale_requests": [{"id": 1, "mentor_id": 1, "created_at": "2026-11-11T17:07:42.798407+00:00"}], "inactive_relationships": [{"id": 1, "status": "active", "last_activity_at": "2026-10-17T17:07:42.798407+00:00"}]}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_alerts_list_stale_requests_and_inactive_relationships`

---

### TC-273: No alerts when every request and relationship is recent

**User stories:** US-22

**API being tested:** `GET /api/v1/admin/alerts`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`

**Expected Output:**
- HTTP Status Code: 200
- JSON: `{"stale_requests": [], "inactive_relationships": []}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"stale_requests": [], "inactive_relationships": []}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_alerts_empty_when_everything_is_recent`

---

### TC-274: A mentor cannot see admin alerts

**User stories:** US-22

**API being tested:** `GET /api/v1/admin/alerts`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <mentor token>`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_alerts_forbidden_for_mentor`

---

### TC-275: Analytics count active mentors and mentees, requests, acceptance rate and sessions

**User stories:** US-21

**API being tested:** `GET /api/v1/admin/analytics`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"active_mentors": 2, "active_mentees": 1, "active_relationships": 1, "requests": 2, "accepted_requests": 1, "acceptance_rate": 0.5, "sessions": 1, "career_goals": [], "popular_interest_areas": [], "insufficient_mentor_availability": [], "participation_trends": [{"month": "2026-11", "relationships_started": 1}], "period": {"start": "0001-01-01T00:00:00+00:00", "end": "2026-11-17T17:07:43.934133+00:00"}}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_analytics_counts_participation`

---

### TC-276: Career goals shared by fewer than 3 students are hidden for privacy

**User stories:** US-21

**API being tested:** `GET /api/v1/admin/analytics`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"active_mentors": 0, "active_mentees": 0, "active_relationships": 0, "requests": 0, "accepted_requests": 0, "acceptance_rate": 0, "sessions": 0, "career_goals": [{"goal": "Job", "count": 3}], "popular_interest_areas": [], "insufficient_mentor_availability": [], "participation_trends": [], "period": {"start": "0001-01-01T00:00:00+00:00", "end": "2026-11-17T17:07:44.351847+00:00"}}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_analytics_hide_groups_smaller_than_three`

---

### TC-277: Domains with fewer than 3 free mentor slots are flagged

**User stories:** US-21

**API being tested:** `GET /api/v1/admin/analytics`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"active_mentors": 2, "active_mentees": 0, "active_relationships": 0, "requests": 0, "accepted_requests": 0, "acceptance_rate": 0, "sessions": 0, "career_goals": [], "popular_interest_areas": [], "insufficient_mentor_availability": [{"domain": "Healthcare", "available_capacity": 1}], "participation_trends": [], "period": {"start": "0001-01-01T00:00:00+00:00", "end": "2026-11-17T17:07:44.607898+00:00"}}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_analytics_flags_domains_with_little_capacity`

---

### TC-278: Analytics can be limited to a date range

**User stories:** US-21

**API being tested:** `GET /api/v1/admin/analytics`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`
- Query: `{"start": "2026-01-01T00:00:00Z", "end": "2026-01-31T23:59:59Z"}`

**Expected Output:**
- HTTP Status Code: 200
- JSON containing: `{"requests": 1}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"active_mentors": 1, "active_mentees": 0, "active_relationships": 0, "requests": 1, "accepted_requests": 0, "acceptance_rate": 0.0, "sessions": 0, "career_goals": [], "popular_interest_areas": [], "insufficient_mentor_availability": [], "participation_trends": [], "period": {"start": "2026-01-01T00:00:00+00:00", "end": "2026-01-31T23:59:59+00:00"}}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_analytics_filtered_by_date_range`

---

### TC-279: A start date after the end date is rejected

**User stories:** US-21

**API being tested:** `GET /api/v1/admin/analytics`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <admin token>`
- Query: `{"start": "2026-02-01T00:00:00Z", "end": "2026-01-01T00:00:00Z"}`

**Expected Output:**
- HTTP Status Code: 422
- JSON: `{"detail": "Start must not be after end"}`

**Actual Output:**
- HTTP Status Code: 422
- JSON: `{"detail": "Start must not be after end"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_analytics_start_after_end_is_rejected`

---

### TC-280: A student cannot see analytics

**User stories:** US-21

**API being tested:** `GET /api/v1/admin/analytics`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Actual Output:**
- HTTP Status Code: 403
- JSON: `{"detail": "Admin access required"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_analytics_forbidden_for_student`

---

### TC-281: A user sees their own notifications, newest first

**User stories:** US-13, US-14

**API being tested:** `GET /api/v1/notifications`

**Inputs:**
- Request Method: GET
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 200

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"items": [{"id": 2, "type": "request_declined", "message": "Your mentoring request was declined.", "entity_id": 1, "is_read": false, "created_at": "2026-11-17T17:07:45.278377+00:00"}]}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_user_lists_own_notifications_newest_first`

---

### TC-282: A user marks a notification as read

**User stories:** US-14

**API being tested:** `POST /api/v1/notifications/1/read`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <mentor token>`

**Expected Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "is_read": true}`

**Actual Output:**
- HTTP Status Code: 200
- JSON: `{"id": 1, "is_read": true}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_mark_notification_read`

---

### TC-283: A user cannot mark another user's notification

**User stories:** US-14

**API being tested:** `POST /api/v1/notifications/1/read`

**Inputs:**
- Request Method: POST
- Header: `Authorization: Bearer <student token>`

**Expected Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Notification not found"}`

**Actual Output:**
- HTTP Status Code: 404
- JSON: `{"detail": "Notification not found"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_cannot_mark_someone_elses_notification`

---

### TC-284: Notifications cannot be read without logging in

**User stories:** US-14

**API being tested:** `GET /api/v1/notifications`

**Inputs:**
- Request Method: GET
- Header: none (not logged in)

**Expected Output:**
- HTTP Status Code: 401

**Actual Output:**
- HTTP Status Code: 401
- JSON: `{"detail": "Not authenticated"}`

**Result:** Success

pytest: `tests/test_api_moderation_insights.py::test_notifications_require_login`

---
