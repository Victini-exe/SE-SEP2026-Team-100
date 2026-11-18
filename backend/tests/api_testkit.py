"""Shared helpers for the API test suite.

Everything here is imported into ``conftest.py``:

* ``api`` fixture - an :class:`Api` object that creates users and data through
  the real endpoints, and records the calls a test is actually about.
* ``--case-report PATH`` - writes every recorded call (inputs, expected output,
  actual output, result) to JSON.  ``tests/generate_test_case_doc.py`` turns
  that JSON into the Milestone 3 test-case document.

Setup calls (registering users, approving mentors, ...) go through the helper
methods and are *not* recorded.  The call under test goes through
``api.call(...)`` and its expectation through ``api.expect(...)``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

API = "/api/v1"
PASSWORD = "password123"

# 100+ characters of real content, the minimum for a mentoring request (US-12).
REQUEST_MESSAGE = (
    "I am preparing to graduate and would like guidance on moving into a data science role, "
    "including which projects to build first."
)
QUESTION_TEXT = "How should I prepare for data science interviews in my final term of the BS degree?"


@dataclass
class Actor:
    """A logged-in user and the bearer header to act as them."""

    id: int
    email: str
    role: str
    label: str
    headers: dict[str, str] = field(repr=False)


@dataclass
class _Call:
    method: str
    path: str
    actor: str | None
    params: dict | None
    json_body: Any
    form: dict | None
    status: int | None = None
    response: Any = None
    expected: dict | None = None


def _body(response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text


def _contains(actual: Any, expected: Any) -> bool:
    """True when every key/value in ``expected`` is present in ``actual``."""
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and _contains(actual[key], value) for key, value in expected.items()
        )
    return actual == expected


class Api:
    def __init__(self, client: TestClient) -> None:
        self.client = client
        self.calls: list[_Call] = []
        self._by_response: dict[int, _Call] = {}
        self._admin: Actor | None = None
        self._counter = 0

    # ------------------------------------------------------------------ recording
    def call(
        self,
        method: str,
        path: str,
        *,
        as_: Actor | None = None,
        json: Any = None,
        data: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
    ):
        """Make the request this test is about and record it for the report."""
        url = path if path.startswith("/health") or path.startswith(API) else f"{API}{path}"
        request_headers = dict(as_.headers) if as_ else {}
        if headers:
            request_headers.update(headers)
        response = self.client.request(
            method.upper(), url, headers=request_headers, json=json, data=data, params=params
        )
        actor = as_.label if as_ else None
        if headers and "Authorization" in headers and not as_:
            actor = "custom token"
        record = _Call(method.upper(), url, actor, params, json, data, response.status_code, _body(response))
        self.calls.append(record)
        self._by_response[id(response)] = record
        return response

    def expect(self, response, status: int, *, body: Any = None, contains: Any = None, note: str | None = None):
        """Record the expected output, then assert the actual output matches it."""
        record = self._by_response.get(id(response))
        if record is not None:
            record.expected = {"status": status, "body": body, "contains": contains, "note": note}
        actual = _body(response)
        assert response.status_code == status, f"expected HTTP {status}, got {response.status_code}: {response.text}"
        if body is not None:
            assert actual == body, f"expected body {body!r}, got {actual!r}"
        if contains is not None:
            assert _contains(actual, contains), f"expected body to contain {contains!r}, got {actual!r}"
        return actual

    # ------------------------------------------------------------------ setup helpers
    def _raw(self, method: str, path: str, actor: Actor | None = None, **kwargs):
        headers = actor.headers if actor else {}
        return self.client.request(method.upper(), f"{API}{path}", headers=headers, **kwargs)

    def _ok(self, response, status: int = 200):
        assert response.status_code == status, f"setup call failed: HTTP {response.status_code} {response.text}"
        return response.json()

    def unique_email(self, prefix: str = "user") -> str:
        return f"{prefix}-{uuid4().hex[:10]}@study.iitm.ac.in"

    def login(self, email: str, password: str = PASSWORD) -> dict[str, str]:
        token = self._ok(self._raw("post", "/auth/login", json={"institute_email": email, "password": password}))
        return {"Authorization": f"Bearer {token['access_token']}"}

    def register(self, role: str = "student", *, name: str | None = None, label: str | None = None) -> Actor:
        self._counter += 1
        email = self.unique_email(role)
        user = self._ok(
            self._raw(
                "post",
                "/auth/register",
                json={"name": name or f"{role.title()} {self._counter}", "institute_email": email, "password": PASSWORD, "role": role},
            ),
            201,
        )
        return Actor(user["id"], email, role, label or role, self.login(email))

    def admin(self, *, label: str = "admin", fresh: bool = False) -> Actor:
        """Administrators cannot self-register, so they are inserted directly (like create_admin.py)."""
        if self._admin is not None and not fresh:
            return self._admin
        from app.api.v1.endpoints.auth import get_password_hash
        from app.db.session import SessionLocal
        from app.models import User

        email = self.unique_email("admin")
        with SessionLocal() as db:
            user = User(name="Program Admin", institute_email=email, password_hash=get_password_hash(PASSWORD), role="admin", account_status="active")
            db.add(user)
            db.commit()
            user_id = user.id
        actor = Actor(user_id, email, "admin", label, self.login(email))
        if not fresh:
            self._admin = actor
        return actor

    def apply(self, mentor: Actor, **fields) -> dict:
        body = {"roll_number": "21f1000001", "graduation_year": 2025, "linked_in_url": "https://www.linkedin.com/in/example"}
        body.update(fields)
        return self._ok(self._raw("post", "/mentors/apply", mentor, json=body), 201)

    def approve(self, application_id: int) -> dict:
        return self._ok(self._raw("post", f"/admin/applications/{application_id}/review", self.admin(), json={"action": "approve"}))

    def mentor(self, *, capacity: int = 1, name: str | None = None, label: str = "mentor", **profile) -> Actor:
        """A mentor whose application is approved and whose profile is set up."""
        actor = self.register("mentor", name=name, label=label)
        self.approve(self.apply(actor)["id"])
        body = {"max_mentee_capacity": capacity, "pause_status": "active", "guidance_types": "Career mentoring", "preferred_languages": "English"}
        body.update(profile)
        self._ok(self._raw("put", "/mentors/me/profile", actor, json=body))
        return actor

    def student(self, *, label: str = "student", name: str | None = None, **profile) -> Actor:
        actor = self.register("student", name=name, label=label)
        if profile:
            self._ok(self._raw("put", "/students/me/profile", actor, json=profile))
        return actor

    def question(self, student: Actor, text: str = QUESTION_TEXT) -> dict:
        return self._ok(self._raw("post", "/students/questions", student, json={"question_text": text}), 201)

    def send_request(self, student: Actor, mentor: Actor, message: str = REQUEST_MESSAGE) -> dict:
        return self._ok(self._raw("post", "/requests", student, json={"mentor_id": mentor.id, "personal_message": message}), 201)

    def decide(self, mentor: Actor, request_id: int, action: str = "accept") -> dict:
        return self._ok(self._raw("post", f"/requests/{request_id}/decision", mentor, json={"action": action}))

    def relationship(self, student: Actor, mentor: Actor) -> int:
        """Create an accepted mentoring relationship and return its id."""
        request_id = self.send_request(student, mentor)["id"]
        self.decide(mentor, request_id)
        items = self._ok(self._raw("get", "/relationships", student))["items"]
        return next(item["id"] for item in items if item["mentor_id"] == mentor.id and item["status"] == "active")

    def session(self, relationship_id: int, proposer: Actor, when: datetime, tz: str = "UTC") -> dict:
        body = {"scheduled_for": when.isoformat(), "timezone": tz}
        return self._ok(self._raw("post", f"/relationships/{relationship_id}/sessions", proposer, json=body), 201)

    def suspend(self, user: Actor, reason: str = "Repeated spam reported by several students.") -> dict:
        return self._ok(self._raw("post", f"/admin/users/{user.id}/suspend", self.admin(), json={"reason": reason}))

    def interest(self, name: str) -> int:
        from app.db.session import SessionLocal
        from app.models import InterestArea

        with SessionLocal() as db:
            row = InterestArea(name=name, category="Domain")
            db.add(row)
            db.commit()
            return row.id

    def update_row(self, model, row_id: int, **values) -> None:
        """Change stored values directly, e.g. to move a request 8 days into the past."""
        from app.db.session import SessionLocal

        with SessionLocal() as db:
            row = db.get(model, row_id)
            for key, value in values.items():
                setattr(row, key, value)
            db.commit()

    def fetch(self, model, **filters):
        from app.db.session import SessionLocal

        with SessionLocal() as db:
            return db.query(model).filter_by(**filters).all()

    def notifications(self, user: Actor) -> list[dict]:
        return self._ok(self._raw("get", "/notifications", user))["items"]


@pytest.fixture
def api():
    from app.main import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield Api(test_client)


# ---------------------------------------------------------------------- reporting
_RESULTS: list[dict] = []


def pytest_addoption(parser):
    parser.addoption(
        "--case-report",
        action="store",
        default=None,
        help="Write recorded API test cases (inputs, expected/actual output, result) to this JSON file.",
    )


def _doc_parts(item) -> tuple[str, str, list[str]]:
    doc = (getattr(item.obj, "__doc__", None) or "").strip()
    lines = [line.strip() for line in doc.splitlines() if line.strip()]
    title = lines[0] if lines else item.name.replace("_", " ")
    stories: list[str] = []
    description: list[str] = []
    for line in lines[1:]:
        if line.lower().startswith("stories:"):
            stories = [part.strip() for part in line.split(":", 1)[1].split(",") if part.strip()]
        else:
            description.append(line)
    return title, " ".join(description), stories


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" and not (report.when == "setup" and report.failed):
        return
    title, description, stories = _doc_parts(item)
    api_obj = item.funcargs.get("api") if hasattr(item, "funcargs") else None
    if hasattr(report, "wasxfail"):
        result = "Fail"
        known_defect = report.wasxfail.replace("reason: ", "")
    else:
        result = "Success" if report.passed else "Fail"
        known_defect = None
    _RESULTS.append(
        {
            "nodeid": item.nodeid,
            "module": item.module.__name__ if item.module else "",
            "title": title,
            "description": description,
            "stories": stories,
            "result": result,
            "known_defect": known_defect,
            "error": None if report.passed or hasattr(report, "wasxfail") else str(report.longrepr).splitlines()[-1][:500],
            "calls": [
                {
                    "method": c.method,
                    "path": c.path,
                    "actor": c.actor,
                    "params": c.params,
                    "json": c.json_body,
                    "form": c.form,
                    "status": c.status,
                    "response": c.response,
                    "expected": c.expected,
                }
                for c in (api_obj.calls if isinstance(api_obj, Api) else [])
            ],
        }
    )


def pytest_sessionfinish(session):
    target = session.config.getoption("--case-report")
    if not target:
        return
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(), "cases": _RESULTS}
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
