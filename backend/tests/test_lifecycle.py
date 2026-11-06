from datetime import datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException

from app.db.session import SessionLocal
from app.models import AuditLog
from app.api.v1.endpoints.lifecycle import _session_time_utc


def register(client, role):
    email = f"{role}-{uuid4().hex}@study.iitm.ac.in"
    if role == "admin":
        from app.api.v1.endpoints.auth import get_password_hash
        from app.models import User

        with SessionLocal() as db:
            db.add(User(
                name="Admin",
                institute_email=email,
                password_hash=get_password_hash("password123"),
                role="admin",
                account_status="active",
            ))
            db.commit()
        login = client.post("/api/v1/auth/login", json={"institute_email": email, "password": "password123"})
        assert login.status_code == 200, login.text
        return email, {"Authorization": f"Bearer {login.json()['access_token']}"}
    response = client.post(
        "/api/v1/auth/register",
        json={"name": role.title(), "institute_email": email, "password": "password123", "role": role},
    )
    assert response.status_code == 201, response.text
    login = client.post("/api/v1/auth/login", json={"institute_email": email, "password": "password123"})
    assert login.status_code == 200, login.text
    return email, {"Authorization": f"Bearer {login.json()['access_token']}"}


def approved_mentor(client, mentor_headers, admin_headers):
    application = client.post("/api/v1/mentors/apply", headers=mentor_headers, json={})
    assert application.status_code == 201, application.text
    result = client.post(
        f"/api/v1/admin/applications/{application.json()['id']}/review",
        headers=admin_headers,
        json={"action": "approve"},
    )
    assert result.status_code == 200, result.text
    profile = client.put(
        "/api/v1/mentors/me/profile",
        headers=mentor_headers,
        json={"max_mentee_capacity": 1, "pause_status": "active"},
    )
    assert profile.status_code == 200, profile.text
    return profile.json()["user_id"]


def test_request_withdraw_accept_sessions_messages_and_closure(client):
    _, student_headers = register(client, "student")
    _, mentor_headers = register(client, "mentor")
    _, admin_headers = register(client, "admin")
    mentor_id = approved_mentor(client, mentor_headers, admin_headers)
    question = client.post(
        "/api/v1/students/questions",
        headers=student_headers,
        json={"question_text": "How can I transition into a data science role after graduation?"},
    )
    assert question.status_code == 201, question.text
    request_payload = {
        "mentor_id": mentor_id,
        "personal_message": "I am looking for guidance about transitioning into a data science role and preparing a focused portfolio.",
        "career_question_id": question.json()["id"],
    }

    short_message = {**request_payload, "personal_message": "Too short"}
    assert client.post("/api/v1/requests", headers=student_headers, json=short_message).status_code == 422
    created = client.post("/api/v1/requests", headers=student_headers, json=request_payload)
    assert created.status_code == 201, created.text
    request_id = created.json()["id"]
    assert client.post("/api/v1/requests", headers=student_headers, json=request_payload).status_code == 409

    incoming = client.get("/api/v1/requests", headers=mentor_headers).json()["items"]
    assert incoming[0]["student"]["career_question"] == question.json()["question_text"]
    assert client.post(f"/api/v1/requests/{request_id}/withdraw", headers=student_headers).json()["status"] == "withdrawn"
    assert client.post(
        f"/api/v1/requests/{request_id}/decision",
        headers=mentor_headers,
        json={"action": "accept"},
    ).status_code == 409

    request = client.post("/api/v1/requests", headers=student_headers, json=request_payload)
    assert request.status_code == 201, request.text
    accepted = client.post(
        f"/api/v1/requests/{request.json()['id']}/decision",
        headers=mentor_headers,
        json={"action": "accept"},
    )
    assert accepted.status_code == 200, accepted.text
    relationship_id = client.get("/api/v1/relationships", headers=student_headers).json()["items"][0]["id"]

    sent = client.post(
        f"/api/v1/relationships/{relationship_id}/messages",
        headers=student_headers,
        json={"content": "Thank you for accepting my request."},
    )
    assert sent.status_code == 201, sent.text
    history = client.get(f"/api/v1/relationships/{relationship_id}/messages", headers=mentor_headers)
    assert history.status_code == 200
    assert history.json()["items"][0]["content"] == "Thank you for accepting my request."
    assert client.get(f"/api/v1/relationships/{relationship_id}/messages", headers=admin_headers).status_code == 404
    assert client.get("/api/v1/mentors/search?page=1&page_size=30").json()["total"] == 0

    meeting_time = datetime.now(timezone.utc) - timedelta(days=3)
    local_meeting_time = meeting_time.astimezone(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
    proposed = client.post(
        f"/api/v1/relationships/{relationship_id}/sessions",
        headers=student_headers,
        json={"scheduled_for": local_meeting_time.isoformat(), "timezone": "Asia/Kolkata"},
    )
    assert proposed.status_code == 201, proposed.text
    assert datetime.fromisoformat(proposed.json()["scheduled_for"]) == meeting_time
    session_id = proposed.json()["id"]
    confirmed = client.post(
        f"/api/v1/sessions/{session_id}/decision",
        headers=mentor_headers,
        json={"action": "confirm"},
    )
    assert confirmed.status_code == 200 and confirmed.json()["status"] == "confirmed"
    note = client.post(
        f"/api/v1/sessions/{session_id}/notes",
        headers=mentor_headers,
        json={"notes": "Discussed portfolio scope and interview preparation."},
    )
    assert note.status_code == 201 and note.json()["submitted_late"] is True
    assert client.get(f"/api/v1/sessions/{session_id}/notes", headers=student_headers).json()["items"][0]["notes"]

    suspended = client.post(
        f"/api/v1/admin/users/{mentor_id}/suspend",
        headers=admin_headers,
        json={"reason": "A temporary review is required for this account."},
    )
    assert suspended.status_code == 200 and suspended.json()["suspended_relationships"] == 1
    blocked = client.post(
        f"/api/v1/relationships/{relationship_id}/messages",
        headers=student_headers,
        json={"content": "This must not reach a suspended account."},
    )
    assert blocked.status_code == 409
    resumed = client.post(
        f"/api/v1/admin/users/{mentor_id}/reactivate",
        headers=admin_headers,
        json={"reason": "Administrator review is complete and account is restored."},
    )
    assert resumed.status_code == 200

    closed = client.post(
        f"/api/v1/relationships/{relationship_id}/close",
        headers=student_headers,
        json={"reason": "GOAL_ACHIEVED"},
    )
    assert closed.status_code == 200 and closed.json()["status"] == "closed"
    assert client.post(
        f"/api/v1/relationships/{relationship_id}/messages",
        headers=student_headers,
        json={"content": "This should no longer send."},
    ).status_code == 409
    assert client.get("/api/v1/mentors/search?page=1&page_size=30").json()["total"] == 1


def test_reporting_and_admin_account_suspension_are_audited(client):
    _, reporter_headers = register(client, "student")
    target_email, target_headers = register(client, "mentor")
    _, admin_headers = register(client, "admin")
    from app.models import User

    with SessionLocal() as db:
        target = db.query(User).filter(User.institute_email == target_email).one()
        target_id = target.id

    report = client.post(
        "/api/v1/reports",
        headers=reporter_headers,
        json={
            "target_user_id": target_id,
            "category": "SPAM",
            "description": "This account sent repeated unsolicited promotional messages.",
        },
    )
    assert report.status_code == 201, report.text
    assert client.post(
        "/api/v1/reports",
        headers=reporter_headers,
        json={
            "target_user_id": target_id,
            "category": "SPAM",
            "description": "This account sent repeated unsolicited promotional messages.",
        },
    ).status_code == 409
    review = client.post(
        f"/api/v1/admin/reports/{report.json()['id']}/review",
        headers=admin_headers,
        json={"status": "resolved", "admin_review_notes": "Reviewed and actioned."},
    )
    assert review.status_code == 200, review.text
    assert client.get("/api/v1/admin/reports", headers=reporter_headers).status_code == 403
    analytics = client.get("/api/v1/admin/analytics", headers=admin_headers)
    assert analytics.status_code == 200, analytics.text
    assert "participation_trends" in analytics.json()

    suspended = client.post(
        f"/api/v1/admin/users/{target_id}/suspend",
        headers=admin_headers,
        json={"reason": "Repeated policy violations were confirmed by review."},
    )
    assert suspended.status_code == 200
    failed_login = client.post(
        "/api/v1/auth/login",
        json={"institute_email": target_email, "password": "password123"},
    )
    assert failed_login.status_code == 403
    reactivated = client.post(
        f"/api/v1/admin/users/{target_id}/reactivate",
        headers=admin_headers,
        json={"reason": "The appeal was reviewed and the account may return."},
    )
    assert reactivated.status_code == 200
    assert client.post(
        "/api/v1/auth/login",
        json={"institute_email": target_email, "password": "password123"},
    ).status_code == 200
    with SessionLocal() as db:
        actions = db.query(AuditLog.action).filter(AuditLog.entity_id == target_id).all()
    assert {row[0] for row in actions} >= {"account_suspended", "account_reactivated"}


def test_three_pending_request_limit_and_lazy_expiration(client):
    _, student_headers = register(client, "student")
    _, admin_headers = register(client, "admin")
    mentor_ids = []
    for _ in range(4):
        _, mentor_headers = register(client, "mentor")
        mentor_ids.append(approved_mentor(client, mentor_headers, admin_headers))

    requests = []
    for mentor_id in mentor_ids[:3]:
        response = client.post(
            "/api/v1/requests",
            headers=student_headers,
            json={
                "mentor_id": mentor_id,
                "personal_message": "I would appreciate your advice on planning a career transition, identifying suitable roles, and building a strong portfolio for the next application cycle.",
            },
        )
        assert response.status_code == 201, response.text
        requests.append(response.json()["id"])

    over_limit = client.post(
        "/api/v1/requests",
        headers=student_headers,
        json={
            "mentor_id": mentor_ids[3],
            "personal_message": "I would appreciate your advice on planning a career transition, identifying suitable roles, and building a strong portfolio for the next application cycle.",
        },
    )
    assert over_limit.status_code == 409

    from app.models import MentoringRequest

    with SessionLocal() as db:
        old_request = db.query(MentoringRequest).filter(MentoringRequest.id == requests[0]).one()
        old_request.created_at = datetime.now(timezone.utc) - timedelta(days=8)
        db.commit()
    refreshed = client.get("/api/v1/requests", headers=student_headers)
    statuses = {item["id"]: item["status"] for item in refreshed.json()["items"]}
    assert statuses[requests[0]] == "expired"
    assert statuses[requests[1]] == "pending"


def test_timezone_conversion_rejects_ambiguous_and_nonexistent_local_times():
    with pytest.raises(HTTPException) as ambiguous:
        _session_time_utc(datetime(2026, 11, 1, 1, 30), "America/New_York")
    assert "Ambiguous local time" in ambiguous.value.detail
    with pytest.raises(HTTPException) as nonexistent:
        _session_time_utc(datetime(2026, 3, 8, 2, 30), "America/New_York")
    assert "does not exist" in nonexistent.value.detail
    instant = _session_time_utc(datetime(2026, 6, 1, 12, 0), "Asia/Kolkata")
    assert instant == datetime(2026, 6, 1, 6, 30, tzinfo=timezone.utc)
