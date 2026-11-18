# Milestone 3 - API test suite

Pytest tests for every backend endpoint (all 42 method + route pairs under `/api/v1` and `/health`)
and the logic behind them: permissions, validation, state changes, matching scores and notifications.

Result of the last run: **286 passed, 9 expected failures, about 50 seconds**.
The 9 expected failures are real defects in the API. Each one is marked `xfail(strict=True)`,
so it shows as a failure in the report without breaking the build, and it turns into an error
once the defect is fixed (remove the mark then).

## Files

| File | What it is |
|---|---|
| `backend/tests/test_api_*.py` (8 files) | The tests, one file per module |
| `backend/tests/api_testkit.py` | Shared helpers (`api` fixture, users, sample data) and the recorder behind `--case-report` |
| `backend/tests/conftest.py` | Changed: clears the database before each test; uses a fast bcrypt setting in tests only (8 min -> 50 s). The existing 11 tests still pass. |
| `backend/tests/generate_test_case_doc.py` | Builds the test-case document from a run |
| `docs/testing/API_TEST_CASES.pdf` / `.md` | 284 test cases in the course format: API, Inputs, Expected output, Actual output, Result |
| `docs/testing/pytest-output.txt` | Full pytest output (`-v -rxX`) |
| `docs/testing/api-test-results.json` | Raw data the document was built from |

## Adding it to the repo

Unzip at the root of the repository (it keeps the repo's folder layout), then:

```bash
git checkout -b test/api-test-suite
git add backend/tests docs/testing
git commit -m "Add Milestone 3 API test suite"
git push -u origin test/api-test-suite
```

## Running

```bash
cd backend
python -m pytest -v -rxX
```

To rebuild the test-case document after code changes:

```bash
cd backend
python -m pytest tests --case-report ../docs/testing/api-test-results.json
python tests/generate_test_case_doc.py ../docs/testing/api-test-results.json ../docs/testing/API_TEST_CASES.md
```

## Defects found

| API | Defect |
|---|---|
| `GET /matching/recommendations` -> `POST /requests` | Recommendations return the mentor *profile* id, but requests expect the mentor *user* id, so requesting a recommended mentor fails (404) |
| `POST /mentors/apply` | An empty application is accepted; US-02 requires roll number, graduation year and LinkedIn |
| `PUT /mentors/me/profile` | An unknown `pause_status` returns 500 instead of 422 |
| `PUT /mentors/me/profile` | An unknown `experience_level` returns 500 instead of 422 |
| `POST /admin/applications/{id}/review` | An already decided application can be reviewed again; rejecting after approving leaves the mentor active |
| `GET /mentors/{id}` | A suspended mentor's public profile is still visible |
| `GET /mentors/search` | Works without logging in |
| `POST /auth/logout` | The old token keeps working after logout |
| `PUT /students/me/profile` | Profile changes are not saved with a date (US-06); `profile_history` is never written |
