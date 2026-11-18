"""Relationships, sessions, session notes and messages.

GET /relationships, POST /relationships/{id}/close,
POST/GET /relationships/{id}/sessions, POST /sessions/{id}/decision,
POST/GET /sessions/{id}/notes, POST/GET /relationships/{id}/messages.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.models import Message, Notification

NOW = datetime.now(timezone.utc)


def _pair(api, **mentor_kwargs):
    student, mentor = api.register("student"), api.mentor(**mentor_kwargs)
    return student, mentor, api.relationship(student, mentor)


# ------------------------------------------------------------------ GET /relationships


def test_student_and_mentor_both_see_relationship(api):
    """Both sides see the active relationship with names and context
    Stories: US-14, US-15"""
    data = api.interest("Data Science")
    student = api.student(name="Kiran", career_goal="Job", interest_area_ids=[data])
    api.question(student)
    mentor = api.mentor(name="Lakshmi", career_history="5 years at TCS", expertise_area_ids=[data])
    relationship_id = api.relationship(student, mentor)
    body = api.expect(api.call("get", "/relationships", as_=mentor), 200)
    assert body["items"][0] == {
        **body["items"][0],
        "id": relationship_id,
        "student_name": "Kiran",
        "mentor_name": "Lakshmi",
        "status": "active",
        "student_career_goal": "Job",
        "student_interests": ["Data Science"],
        "mentor_expertise": ["Data Science"],
        "mentor_career_history": "5 years at TCS",
    }
    assert [r["id"] for r in api._raw("get", "/relationships", student).json()["items"]] == [relationship_id]


def test_mentor_sees_all_assigned_mentees(api):
    """A mentor sees every mentee assigned to them
    Stories: US-15"""
    mentor = api.mentor(capacity=3)
    ids = {api.relationship(api.register("student", label=f"student {n}"), mentor) for n in range(3)}
    body = api.expect(api.call("get", "/relationships", as_=mentor), 200)
    assert {item["id"] for item in body["items"]} == ids


def test_outsider_sees_no_relationships(api):
    """A user who is not part of a relationship does not see it
    Stories: US-15"""
    _pair(api)
    api.expect(api.call("get", "/relationships", as_=api.register("student", label="student B")), 200, body={"items": []})


def test_relationships_require_login(api):
    """Relationships cannot be listed without logging in
    Stories: US-14"""
    api.expect(api.call("get", "/relationships"), 401)


# ------------------------------------------------------------------ POST /relationships/{id}/close


@pytest.mark.parametrize("reason", ["GOAL_ACHIEVED", "NO_LONGER_NEEDED", "NOT_A_GOOD_FIT"])
def test_close_relationship_with_reason(api, reason):
    """Either side closes the relationship with a reason
    Stories: US-17"""
    student, mentor, relationship_id = _pair(api)
    body = api.expect(api.call("post", f"/relationships/{relationship_id}/close", as_=student, json={"reason": reason}), 200, contains={"id": relationship_id, "status": "closed"})
    assert body["ended_at"]
    closed = api._raw("get", "/relationships", mentor).json()["items"][0]
    assert closed["closure_reason"] == reason and closed["status"] == "closed"
    assert "relationship_closed" in [n["type"] for n in api.notifications(mentor)]


def test_mentor_can_close_relationship(api):
    """A mentor can close the relationship too
    Stories: US-17"""
    student, mentor, relationship_id = _pair(api)
    api.expect(api.call("post", f"/relationships/{relationship_id}/close", as_=mentor, json={"reason": "GOAL_ACHIEVED"}), 200, contains={"status": "closed"})
    assert "relationship_closed" in [n["type"] for n in api.notifications(student)]


def test_closing_frees_mentor_slot_immediately(api):
    """Closing a relationship frees the mentor's slot at once
    Stories: US-17, US-08"""
    student, mentor, relationship_id = _pair(api, capacity=1)
    api._ok(api._raw("post", f"/relationships/{relationship_id}/close", student, json={"reason": "GOAL_ACHIEVED"}))
    res = api.call("post", "/requests", as_=api.register("student", label="student B"), json={"mentor_id": mentor.id, "personal_message": "n" * 120})
    api.expect(res, 201)


def test_close_with_other_needs_explanation(api):
    """Closing with reason OTHER needs an explanation
    Stories: US-17"""
    student, _, relationship_id = _pair(api)
    res = api.call("post", f"/relationships/{relationship_id}/close", as_=student, json={"reason": "OTHER", "explanation": "   "})
    api.expect(res, 422, body={"detail": "An explanation is required for OTHER"})


def test_close_with_other_and_explanation(api):
    """Closing with reason OTHER and an explanation works
    Stories: US-17"""
    student, _, relationship_id = _pair(api)
    payload = {"reason": "OTHER", "explanation": "I moved abroad for my master's degree."}
    api.expect(api.call("post", f"/relationships/{relationship_id}/close", as_=student, json=payload), 200, contains={"status": "closed"})


def test_close_rejects_unknown_reason(api):
    """An unknown closure reason is rejected
    Stories: US-17"""
    student, _, relationship_id = _pair(api)
    api.expect(api.call("post", f"/relationships/{relationship_id}/close", as_=student, json={"reason": "BORED"}), 422)


def test_close_twice_is_refused(api):
    """A closed relationship cannot be closed again
    Stories: US-17"""
    student, _, relationship_id = _pair(api)
    api._ok(api._raw("post", f"/relationships/{relationship_id}/close", student, json={"reason": "GOAL_ACHIEVED"}))
    res = api.call("post", f"/relationships/{relationship_id}/close", as_=student, json={"reason": "GOAL_ACHIEVED"})
    api.expect(res, 409, body={"detail": "Relationship is not active"})


def test_outsider_cannot_close(api):
    """Someone outside the relationship cannot close it
    Stories: US-17"""
    _, _, relationship_id = _pair(api)
    res = api.call("post", f"/relationships/{relationship_id}/close", as_=api.register("student", label="student B"), json={"reason": "GOAL_ACHIEVED"})
    api.expect(res, 404, body={"detail": "Relationship not found"})


# ------------------------------------------------------------------ POST /relationships/{id}/sessions


def test_propose_session_in_local_time_zone(api):
    """A session proposed in IST is stored in UTC and the other side is told
    Stories: US-18"""
    student, mentor, relationship_id = _pair(api)
    payload = {"scheduled_for": "2026-12-05T19:30:00", "timezone": "Asia/Kolkata", "meeting_link": "https://meet.google.com/abc-defg-hij"}
    res = api.call("post", f"/relationships/{relationship_id}/sessions", as_=student, json=payload)
    api.expect(res, 201, contains={"scheduled_for": "2026-12-05T14:00:00+00:00", "proposer_timezone": "Asia/Kolkata", "status": "proposed", "meeting_link": payload["meeting_link"]})
    assert "session_proposed" in [n["type"] for n in api.notifications(mentor)]


def test_propose_session_with_explicit_offset(api):
    """A time with an explicit UTC offset is converted to UTC
    Stories: US-18"""
    _, mentor, relationship_id = _pair(api)
    payload = {"scheduled_for": "2026-12-05T09:00:00-05:00", "timezone": "America/New_York"}
    res = api.call("post", f"/relationships/{relationship_id}/sessions", as_=mentor, json=payload)
    api.expect(res, 201, contains={"scheduled_for": "2026-12-05T14:00:00+00:00"})


@pytest.mark.parametrize(
    "payload,detail",
    [
        ({"scheduled_for": "2026-12-05T19:30:00", "timezone": "Mars/Olympus"}, "Unknown timezone"),
        ({"scheduled_for": "2026-03-08T02:30:00", "timezone": "America/New_York"}, "Local time does not exist in this timezone"),
        ({"scheduled_for": "2026-11-01T01:30:00", "timezone": "America/New_York"}, "Ambiguous local time; include an explicit UTC offset"),
    ],
    ids=["unknown-zone", "skipped-by-dst", "repeated-by-dst"],
)
def test_propose_session_rejects_bad_local_times(api, payload, detail):
    """Unknown zones and times that do not exist or happen twice (DST) are rejected
    Stories: US-18"""
    student, _, relationship_id = _pair(api)
    api.expect(api.call("post", f"/relationships/{relationship_id}/sessions", as_=student, json=payload), 422, body={"detail": detail})


def test_propose_session_needs_time_and_zone(api):
    """A proposal without a time or time zone is rejected
    Stories: US-18"""
    student, _, relationship_id = _pair(api)
    api.expect(api.call("post", f"/relationships/{relationship_id}/sessions", as_=student, json={"timezone": "UTC"}), 422)


def test_propose_session_on_closed_relationship(api):
    """Sessions cannot be proposed after the relationship is closed
    Stories: US-18"""
    student, _, relationship_id = _pair(api)
    api._ok(api._raw("post", f"/relationships/{relationship_id}/close", student, json={"reason": "GOAL_ACHIEVED"}))
    res = api.call("post", f"/relationships/{relationship_id}/sessions", as_=student, json={"scheduled_for": "2026-12-05T10:00:00", "timezone": "UTC"})
    api.expect(res, 409, body={"detail": "Relationship is not active"})


def test_outsider_cannot_propose_session(api):
    """Someone outside the relationship cannot propose a session
    Stories: US-18"""
    _, _, relationship_id = _pair(api)
    res = api.call("post", f"/relationships/{relationship_id}/sessions", as_=api.register("student", label="student B"), json={"scheduled_for": "2026-12-05T10:00:00", "timezone": "UTC"})
    api.expect(res, 404, body={"detail": "Relationship not found"})


# ------------------------------------------------------------------ GET /relationships/{id}/sessions


def test_list_sessions_latest_first(api):
    """Both sides list the sessions, latest first
    Stories: US-18"""
    student, mentor, relationship_id = _pair(api)
    early = api.session(relationship_id, student, NOW + timedelta(days=2))
    late = api.session(relationship_id, mentor, NOW + timedelta(days=9))
    body = api.expect(api.call("get", f"/relationships/{relationship_id}/sessions", as_=mentor), 200)
    assert [s["id"] for s in body["items"]] == [late["id"], early["id"]]


def test_outsider_cannot_list_sessions(api):
    """Someone outside the relationship cannot list its sessions
    Stories: US-18"""
    _, _, relationship_id = _pair(api)
    api.expect(api.call("get", f"/relationships/{relationship_id}/sessions", as_=api.admin()), 404, body={"detail": "Relationship not found"})


# ------------------------------------------------------------------ POST /sessions/{id}/decision


@pytest.mark.parametrize("action,status", [("confirm", "confirmed"), ("unavailable", "unavailable")])
def test_other_side_confirms_or_marks_unavailable(api, action, status):
    """The other participant confirms a proposal or marks it not available
    Stories: US-18"""
    student, mentor, relationship_id = _pair(api)
    session = api.session(relationship_id, student, NOW + timedelta(days=2))
    api.expect(api.call("post", f"/sessions/{session['id']}/decision", as_=mentor, json={"action": action}), 200, contains={"id": session["id"], "status": status})


def test_proposer_cannot_confirm_own_proposal(api):
    """The person who proposed cannot confirm their own proposal
    Stories: US-18"""
    student, _, relationship_id = _pair(api)
    session = api.session(relationship_id, student, NOW + timedelta(days=2))
    res = api.call("post", f"/sessions/{session['id']}/decision", as_=student, json={"action": "confirm"})
    api.expect(res, 409, body={"detail": "Only the other participant may decide a proposal"})


def test_proposer_cancels_session(api):
    """The proposer can cancel a session
    Stories: US-18"""
    student, _, relationship_id = _pair(api)
    session = api.session(relationship_id, student, NOW + timedelta(days=2))
    api.expect(api.call("post", f"/sessions/{session['id']}/decision", as_=student, json={"action": "cancel"}), 200, contains={"status": "cancelled"})


def test_other_side_cannot_cancel(api):
    """Only the proposer can cancel
    Stories: US-18"""
    student, mentor, relationship_id = _pair(api)
    session = api.session(relationship_id, student, NOW + timedelta(days=2))
    res = api.call("post", f"/sessions/{session['id']}/decision", as_=mentor, json={"action": "cancel"})
    api.expect(res, 409, body={"detail": "Only the proposer may cancel this session"})


def test_complete_past_confirmed_session(api):
    """A confirmed session in the past can be marked completed
    Stories: US-18, US-20"""
    student, mentor, relationship_id = _pair(api)
    session = api.session(relationship_id, student, NOW - timedelta(hours=2))
    api._ok(api._raw("post", f"/sessions/{session['id']}/decision", mentor, json={"action": "confirm"}))
    api.expect(api.call("post", f"/sessions/{session['id']}/decision", as_=student, json={"action": "complete"}), 200, contains={"status": "completed"})


def test_future_session_cannot_be_completed(api):
    """A session that has not happened yet cannot be completed
    Stories: US-18"""
    student, mentor, relationship_id = _pair(api)
    session = api.session(relationship_id, student, NOW + timedelta(days=1))
    api._ok(api._raw("post", f"/sessions/{session['id']}/decision", mentor, json={"action": "confirm"}))
    res = api.call("post", f"/sessions/{session['id']}/decision", as_=student, json={"action": "complete"})
    api.expect(res, 409, body={"detail": "Only past confirmed sessions can be completed"})


def test_unconfirmed_session_cannot_be_completed(api):
    """A session that was never confirmed cannot be completed
    Stories: US-18"""
    student, _, relationship_id = _pair(api)
    session = api.session(relationship_id, student, NOW - timedelta(hours=2))
    res = api.call("post", f"/sessions/{session['id']}/decision", as_=student, json={"action": "complete"})
    api.expect(res, 409, body={"detail": "Only past confirmed sessions can be completed"})


def test_session_decision_validation_and_unknown_session(api):
    """Unknown actions are rejected and unknown sessions return 404
    Stories: US-18"""
    student, _, relationship_id = _pair(api)
    session = api.session(relationship_id, student, NOW + timedelta(days=1))
    api.expect(api.call("post", f"/sessions/{session['id']}/decision", as_=student, json={"action": "reschedule"}), 422)
    api.expect(api.call("post", "/sessions/9999/decision", as_=student, json={"action": "confirm"}), 404, body={"detail": "Session not found"})


def test_session_decision_after_relationship_closed(api):
    """Session decisions stop once the relationship is closed
    Stories: US-17, US-18"""
    student, mentor, relationship_id = _pair(api)
    session = api.session(relationship_id, student, NOW + timedelta(days=1))
    api._ok(api._raw("post", f"/relationships/{relationship_id}/close", student, json={"reason": "GOAL_ACHIEVED"}))
    res = api.call("post", f"/sessions/{session['id']}/decision", as_=mentor, json={"action": "confirm"})
    api.expect(res, 409, body={"detail": "Relationship is not active"})


# ------------------------------------------------------------------ POST/GET /sessions/{id}/notes


def test_add_notes_and_action_items_after_session(api):
    """After a session either side records notes and action items with a due date
    Stories: US-20"""
    student, mentor, relationship_id = _pair(api)
    session = api.session(relationship_id, student, NOW - timedelta(hours=3))
    payload = {"notes": "Discussed portfolio projects and the resume.", "action_items": "Build one end-to-end ML project", "due_at": "2026-12-15T12:00:00+00:00"}
    res = api.call("post", f"/sessions/{session['id']}/notes", as_=mentor, json=payload)
    api.expect(res, 201, contains={"notes": payload["notes"], "action_items": payload["action_items"], "due_at": payload["due_at"], "submitted_late": False})


def test_notes_after_48_hours_are_flagged_late(api):
    """Notes added more than 48 hours after the session are flagged as late
    Stories: US-20"""
    student, _, relationship_id = _pair(api)
    session = api.session(relationship_id, student, NOW - timedelta(hours=49))
    res = api.call("post", f"/sessions/{session['id']}/notes", as_=student, json={"notes": "Late summary of our session."})
    api.expect(res, 201, contains={"submitted_late": True})


def test_notes_before_session_are_refused(api):
    """Notes cannot be added before the session has happened
    Stories: US-20"""
    student, _, relationship_id = _pair(api)
    session = api.session(relationship_id, student, NOW + timedelta(days=1))
    res = api.call("post", f"/sessions/{session['id']}/notes", as_=student, json={"notes": "Too early."})
    api.expect(res, 409, body={"detail": "Notes can be added after the session"})


@pytest.mark.parametrize("payload", [{"notes": ""}, {"notes": "n" * 10001}, {"notes": "ok", "action_items": "a" * 5001}], ids=["empty", "notes-10001", "actions-5001"])
def test_notes_validation(api, payload):
    """Empty or over-long notes are rejected
    Stories: US-20"""
    student, _, relationship_id = _pair(api)
    session = api.session(relationship_id, student, NOW - timedelta(hours=1))
    api.expect(api.call("post", f"/sessions/{session['id']}/notes", as_=student, json=payload), 422)


def test_list_notes_for_participants_only(api):
    """Both participants read the notes; outsiders and admins cannot
    Stories: US-20"""
    student, mentor, relationship_id = _pair(api)
    session = api.session(relationship_id, student, NOW - timedelta(hours=1))
    api._ok(api._raw("post", f"/sessions/{session['id']}/notes", mentor, json={"notes": "Mentor notes."}), 201)
    body = api.expect(api.call("get", f"/sessions/{session['id']}/notes", as_=student), 200)
    assert [n["notes"] for n in body["items"]] == ["Mentor notes."]
    api.expect(api.call("get", f"/sessions/{session['id']}/notes", as_=api.admin()), 404, body={"detail": "Relationship not found"})


# ------------------------------------------------------------------ POST/GET /relationships/{id}/messages


def test_send_message_in_active_relationship(api):
    """A participant sends a message and the other side gets a notification without the text
    Stories: US-19"""
    student, mentor, relationship_id = _pair(api)
    text = "Thank you for accepting. Could we talk about MS applications?"
    res = api.call("post", f"/relationships/{relationship_id}/messages", as_=student, json={"content": text})
    body = api.expect(res, 201)
    assert body["id"] and body["created_at"]
    note = [n for n in api.notifications(mentor) if n["type"] == "new_message"][0]
    assert text not in note["message"]


def test_message_of_2000_characters_accepted(api):
    """A message of exactly 2,000 characters is accepted
    Stories: US-19"""
    student, _, relationship_id = _pair(api)
    api.expect(api.call("post", f"/relationships/{relationship_id}/messages", as_=student, json={"content": "m" * 2000}), 201)


@pytest.mark.parametrize("content", ["m" * 2001, "", "    "], ids=["2001-chars", "empty", "only-spaces"])
def test_message_validation(api, content):
    """Messages over 2,000 characters, empty or blank are rejected
    Stories: US-19"""
    student, _, relationship_id = _pair(api)
    api.expect(api.call("post", f"/relationships/{relationship_id}/messages", as_=student, json={"content": content}), 422)


def test_message_after_close_is_refused(api):
    """Messages cannot be sent once the relationship is closed
    Stories: US-17, US-19"""
    student, _, relationship_id = _pair(api)
    api._ok(api._raw("post", f"/relationships/{relationship_id}/close", student, json={"reason": "GOAL_ACHIEVED"}))
    res = api.call("post", f"/relationships/{relationship_id}/messages", as_=student, json={"content": "Hello again"})
    api.expect(res, 409, body={"detail": "Relationship is not active"})


def test_outsider_cannot_send_message(api):
    """Someone outside the relationship cannot send a message in it
    Stories: US-19"""
    _, _, relationship_id = _pair(api)
    res = api.call("post", f"/relationships/{relationship_id}/messages", as_=api.register("student", label="student B"), json={"content": "Hi"})
    api.expect(res, 404, body={"detail": "Relationship not found"})


def test_read_messages_marks_them_read(api):
    """Reading the conversation marks the reader's incoming messages as read
    Stories: US-19"""
    student, mentor, relationship_id = _pair(api)
    api._ok(api._raw("post", f"/relationships/{relationship_id}/messages", student, json={"content": "First"}), 201)
    api._ok(api._raw("post", f"/relationships/{relationship_id}/messages", mentor, json={"content": "Reply"}), 201)
    body = api.expect(api.call("get", f"/relationships/{relationship_id}/messages", as_=mentor), 200)
    assert [(m["content"], m["is_read"]) for m in body["items"]] == [("First", True), ("Reply", False)]


def test_admin_cannot_read_messages(api):
    """An administrator cannot read private messages
    Stories: US-19, US-21"""
    student, _, relationship_id = _pair(api)
    api._ok(api._raw("post", f"/relationships/{relationship_id}/messages", student, json={"content": "Private"}), 201)
    api.expect(api.call("get", f"/relationships/{relationship_id}/messages", as_=api.admin()), 404, body={"detail": "Relationship not found"})


def test_message_history_still_readable_after_close(api):
    """Message history stays readable after the relationship is closed
    Stories: US-17, US-19"""
    student, _, relationship_id = _pair(api)
    api._ok(api._raw("post", f"/relationships/{relationship_id}/messages", student, json={"content": "Before closing"}), 201)
    api._ok(api._raw("post", f"/relationships/{relationship_id}/close", student, json={"reason": "GOAL_ACHIEVED"}))
    body = api.expect(api.call("get", f"/relationships/{relationship_id}/messages", as_=student), 200)
    assert [m["content"] for m in body["items"]] == ["Before closing"]
    assert len(api.fetch(Message)) == 1 and api.fetch(Notification, notification_type="new_message")
