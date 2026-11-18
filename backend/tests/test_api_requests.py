"""Mentoring requests: POST/GET /requests, POST /requests/{id}/decision, POST /requests/{id}/withdraw."""

from datetime import datetime, timedelta, timezone

import pytest

from api_testkit import REQUEST_MESSAGE
from app.models import MentoringRequest

# ------------------------------------------------------------------ POST /requests


def test_student_sends_request_and_mentor_is_notified(api):
    """A student sends a mentoring request with a personal message
    Stories: US-12"""
    student, mentor = api.register("student"), api.mentor()
    question = api.question(student)
    payload = {"mentor_id": mentor.id, "personal_message": REQUEST_MESSAGE, "career_question_id": question["id"]}
    res = api.call("post", "/requests", as_=student, json=payload)
    api.expect(res, 201, contains={"student_id": student.id, "mentor_id": mentor.id, "status": "pending", "career_question_id": question["id"]})
    assert [n["type"] for n in api.notifications(mentor)] == ["new_request"]


@pytest.mark.parametrize("length", [100, 1000], ids=["exactly-100", "exactly-1000"])
def test_request_message_length_boundaries_accepted(api, length):
    """Personal messages of exactly 100 and 1,000 characters are accepted
    Stories: US-12"""
    student, mentor = api.register("student"), api.mentor()
    res = api.call("post", "/requests", as_=student, json={"mentor_id": mentor.id, "personal_message": "m" * length})
    api.expect(res, 201)


@pytest.mark.parametrize(
    "message",
    ["m" * 99, "m" * 1001, "m" * 40 + " " * 60],
    ids=["99-chars", "1001-chars", "100-chars-mostly-spaces"],
)
def test_request_message_length_boundaries_rejected(api, message):
    """Messages under 100 or over 1,000 characters, or padded with spaces, are rejected
    Stories: US-12"""
    student, mentor = api.register("student"), api.mentor()
    res = api.call("post", "/requests", as_=student, json={"mentor_id": mentor.id, "personal_message": message})
    api.expect(res, 422)


def test_fourth_pending_request_is_refused(api):
    """A student cannot have more than 3 pending requests
    Stories: US-12"""
    student = api.register("student")
    for n in range(3):
        api.send_request(student, api.mentor(label=f"mentor {n + 1}"))
    fourth = api.mentor(label="mentor 4")
    res = api.call("post", "/requests", as_=student, json={"mentor_id": fourth.id, "personal_message": REQUEST_MESSAGE})
    api.expect(res, 409, body={"detail": "At most three mentoring requests may be pending"})


def test_duplicate_pending_request_is_refused(api):
    """A second pending request to the same mentor is refused
    Stories: US-12"""
    student, mentor = api.register("student"), api.mentor(capacity=3)
    api.send_request(student, mentor)
    res = api.call("post", "/requests", as_=student, json={"mentor_id": mentor.id, "personal_message": REQUEST_MESSAGE})
    api.expect(res, 409, body={"detail": "A pending request or active relationship already exists"})


def test_request_to_current_mentor_is_refused(api):
    """A student cannot request a mentor they already have
    Stories: US-12"""
    student, mentor = api.register("student"), api.mentor(capacity=3)
    api.relationship(student, mentor)
    res = api.call("post", "/requests", as_=student, json={"mentor_id": mentor.id, "personal_message": REQUEST_MESSAGE})
    api.expect(res, 409, body={"detail": "A pending request or active relationship already exists"})


def test_request_to_mentor_at_capacity_is_refused(api):
    """A request to a mentor with no free slots is refused
    Stories: US-08, US-12"""
    mentor = api.mentor(capacity=1)
    api.relationship(api.register("student", label="student B"), mentor)
    res = api.call("post", "/requests", as_=api.register("student"), json={"mentor_id": mentor.id, "personal_message": REQUEST_MESSAGE})
    api.expect(res, 409, body={"detail": "Mentor is at capacity"})


def test_request_to_paused_mentor_is_refused(api):
    """A request to a paused mentor is refused
    Stories: US-08, US-12"""
    mentor = api.mentor(pause_status="paused")
    res = api.call("post", "/requests", as_=api.register("student"), json={"mentor_id": mentor.id, "personal_message": REQUEST_MESSAGE})
    api.expect(res, 409, body={"detail": "Mentor is not accepting requests"})


def test_request_to_unverified_mentor_is_refused(api):
    """A request to a mentor who is not yet approved is refused
    Stories: US-03, US-12"""
    mentor = api.register("mentor")
    res = api.call("post", "/requests", as_=api.register("student"), json={"mentor_id": mentor.id, "personal_message": REQUEST_MESSAGE})
    api.expect(res, 404, body={"detail": "Available mentor not found"})


def test_request_to_suspended_mentor_is_refused(api):
    """A request to a suspended mentor is refused
    Stories: US-12, US-24"""
    mentor = api.mentor()
    api.suspend(mentor)
    res = api.call("post", "/requests", as_=api.register("student"), json={"mentor_id": mentor.id, "personal_message": REQUEST_MESSAGE})
    api.expect(res, 404, body={"detail": "Available mentor not found"})


def test_request_to_a_student_id_is_refused(api):
    """Sending a request to a user who is not a mentor is refused
    Stories: US-12"""
    other = api.register("student", label="student B")
    res = api.call("post", "/requests", as_=api.register("student"), json={"mentor_id": other.id, "personal_message": REQUEST_MESSAGE})
    api.expect(res, 404, body={"detail": "Available mentor not found"})


def test_request_with_another_students_question_is_refused(api):
    """A student cannot attach another student's career question
    Stories: US-05, US-12"""
    other_question = api.question(api.register("student", label="student B"))
    student, mentor = api.register("student"), api.mentor()
    payload = {"mentor_id": mentor.id, "personal_message": REQUEST_MESSAGE, "career_question_id": other_question["id"]}
    api.expect(api.call("post", "/requests", as_=student, json=payload), 404, body={"detail": "Career question not found"})


def test_mentor_cannot_send_request(api):
    """A mentor cannot send a mentoring request
    Stories: US-12"""
    mentor = api.mentor()
    res = api.call("post", "/requests", as_=api.mentor(label="mentor B"), json={"mentor_id": mentor.id, "personal_message": REQUEST_MESSAGE})
    api.expect(res, 403, body={"detail": "Student access required"})


def test_student_can_request_again_after_decline(api):
    """After a decline the student may send a new request to the same mentor
    Stories: US-12, US-13"""
    student, mentor = api.register("student"), api.mentor()
    api.decide(mentor, api.send_request(student, mentor)["id"], "decline")
    res = api.call("post", "/requests", as_=student, json={"mentor_id": mentor.id, "personal_message": REQUEST_MESSAGE})
    api.expect(res, 201, contains={"status": "pending"})


# ------------------------------------------------------------------ GET /requests


def test_student_lists_only_own_requests(api):
    """A student sees only their own requests
    Stories: US-14"""
    student, other, mentor = api.register("student"), api.register("student", label="student B"), api.mentor(capacity=3)
    mine = api.send_request(student, mentor)
    api.send_request(other, mentor)
    body = api.expect(api.call("get", "/requests", as_=student), 200)
    assert [item["id"] for item in body["items"]] == [mine["id"]]
    assert "student" not in body["items"][0]


def test_mentor_sees_incoming_requests_with_student_context(api):
    """A mentor sees incoming requests with the student's goal and question
    Stories: US-05, US-13"""
    student = api.student(career_goal="Higher Studies", current_situation="Working professional")
    question = api.question(student)
    mentor = api.mentor()
    api._ok(api._raw("post", "/requests", student, json={"mentor_id": mentor.id, "personal_message": REQUEST_MESSAGE, "career_question_id": question["id"]}), 201)
    body = api.expect(api.call("get", "/requests", as_=mentor), 200)
    assert body["items"][0]["student"] == {
        "name": "Student 1",
        "career_goal": "Higher Studies",
        "current_situation": "Working professional",
        "career_question": question["question_text"],
    }


def test_admin_cannot_list_requests(api):
    """An administrator cannot use the requests list
    Stories: US-14"""
    api.expect(api.call("get", "/requests", as_=api.admin()), 403, body={"detail": "Student or mentor access required"})


def test_request_expires_after_seven_days(api):
    """A request with no answer for 7 days is marked expired and both sides are told
    Stories: US-13, US-14"""
    student, mentor = api.register("student"), api.mentor()
    request = api.send_request(student, mentor)
    api.update_row(MentoringRequest, request["id"], created_at=datetime.now(timezone.utc) - timedelta(days=7, minutes=1))
    body = api.expect(api.call("get", "/requests", as_=student), 200)
    assert body["items"][0]["status"] == "expired"
    assert "request_expired" in [n["type"] for n in api.notifications(student)]
    assert "request_expired" in [n["type"] for n in api.notifications(mentor)]


def test_request_six_days_old_stays_pending(api):
    """A request that is 6 days old is still pending
    Stories: US-13"""
    student, mentor = api.register("student"), api.mentor()
    request = api.send_request(student, mentor)
    api.update_row(MentoringRequest, request["id"], created_at=datetime.now(timezone.utc) - timedelta(days=6))
    body = api.expect(api.call("get", "/requests", as_=student), 200)
    assert body["items"][0]["status"] == "pending"


# ------------------------------------------------------------------ POST /requests/{id}/decision


def test_mentor_accepts_request_and_relationship_starts(api):
    """Accepting a request starts a mentoring relationship and tells the student
    Stories: US-13, US-14, US-15"""
    student, mentor = api.register("student"), api.mentor()
    request = api.send_request(student, mentor)
    res = api.call("post", f"/requests/{request['id']}/decision", as_=mentor, json={"action": "accept"})
    api.expect(res, 200, contains={"id": request["id"], "status": "accepted"})
    relationships = api._raw("get", "/relationships", student).json()["items"]
    assert [(r["mentor_id"], r["status"]) for r in relationships] == [(mentor.id, "active")]
    assert "request_accepted" in [n["type"] for n in api.notifications(student)]


def test_mentor_declines_request_with_reason(api):
    """A mentor declines with an optional reason and the student is told
    Stories: US-13"""
    student, mentor = api.register("student"), api.mentor()
    request = api.send_request(student, mentor)
    payload = {"action": "decline", "decline_reason": "My expertise is in research, not industry jobs."}
    api.expect(api.call("post", f"/requests/{request['id']}/decision", as_=mentor, json=payload), 200, contains={"status": "rejected"})
    item = api._raw("get", "/requests", student).json()["items"][0]
    assert item["decline_reason"] == payload["decline_reason"]
    assert "request_declined" in [n["type"] for n in api.notifications(student)]


def test_mentor_declines_without_reason(api):
    """The decline reason is optional
    Stories: US-13"""
    student, mentor = api.register("student"), api.mentor()
    request = api.send_request(student, mentor)
    api.expect(api.call("post", f"/requests/{request['id']}/decision", as_=mentor, json={"action": "decline"}), 200, contains={"status": "rejected"})


def test_accept_refused_when_mentor_is_full(api):
    """A mentor cannot accept more mentees than their capacity
    Stories: US-08, US-13"""
    mentor = api.mentor(capacity=1)
    first = api.send_request(api.register("student"), mentor)
    second = api.send_request(api.register("student", label="student B"), mentor)
    api.decide(mentor, first["id"])
    res = api.call("post", f"/requests/{second['id']}/decision", as_=mentor, json={"action": "accept"})
    api.expect(res, 409, body={"detail": "Mentor is at capacity"})


def test_accept_refused_when_mentor_paused(api):
    """A paused mentor cannot accept requests
    Stories: US-08, US-13"""
    student, mentor = api.register("student"), api.mentor()
    request = api.send_request(student, mentor)
    api._ok(api._raw("put", "/mentors/me/profile", mentor, json={"max_mentee_capacity": 1, "pause_status": "paused"}))
    res = api.call("post", f"/requests/{request['id']}/decision", as_=mentor, json={"action": "accept"})
    api.expect(res, 409, body={"detail": "Mentor is unavailable"})


def test_decision_on_expired_request_is_refused(api):
    """A request older than 7 days can no longer be accepted
    Stories: US-13"""
    student, mentor = api.register("student"), api.mentor()
    request = api.send_request(student, mentor)
    api.update_row(MentoringRequest, request["id"], created_at=datetime.now(timezone.utc) - timedelta(days=8))
    res = api.call("post", f"/requests/{request['id']}/decision", as_=mentor, json={"action": "accept"})
    api.expect(res, 409, body={"detail": "Request is expired"})


def test_request_cannot_be_decided_twice(api):
    """A request that was already accepted cannot be decided again
    Stories: US-13"""
    student, mentor = api.register("student"), api.mentor()
    request = api.send_request(student, mentor)
    api.decide(mentor, request["id"])
    res = api.call("post", f"/requests/{request['id']}/decision", as_=mentor, json={"action": "decline"})
    api.expect(res, 409, body={"detail": "Request is accepted"})


def test_other_mentor_cannot_decide(api):
    """A mentor cannot decide a request sent to someone else
    Stories: US-13"""
    student, mentor = api.register("student"), api.mentor()
    request = api.send_request(student, mentor)
    res = api.call("post", f"/requests/{request['id']}/decision", as_=api.mentor(label="mentor B"), json={"action": "accept"})
    api.expect(res, 404, body={"detail": "Request not found"})


def test_student_cannot_decide(api):
    """A student cannot accept their own request
    Stories: US-13"""
    student, mentor = api.register("student"), api.mentor()
    request = api.send_request(student, mentor)
    res = api.call("post", f"/requests/{request['id']}/decision", as_=student, json={"action": "accept"})
    api.expect(res, 403, body={"detail": "Mentor access required"})


@pytest.mark.parametrize("payload", [{"action": "maybe"}, {"action": "decline", "decline_reason": "r" * 1001}, {}], ids=["unknown-action", "reason-1001-chars", "missing-action"])
def test_decision_validates_body(api, payload):
    """Unknown actions, missing actions and over-long decline reasons are rejected
    Stories: US-13"""
    student, mentor = api.register("student"), api.mentor()
    request = api.send_request(student, mentor)
    api.expect(api.call("post", f"/requests/{request['id']}/decision", as_=mentor, json=payload), 422)


# ------------------------------------------------------------------ POST /requests/{id}/withdraw


def test_student_withdraws_pending_request(api):
    """A student withdraws a pending request and the mentor is told
    Stories: US-16"""
    student, mentor = api.register("student"), api.mentor()
    request = api.send_request(student, mentor)
    body = api.expect(api.call("post", f"/requests/{request['id']}/withdraw", as_=student), 200, contains={"id": request["id"], "status": "withdrawn"})
    assert body["withdrawn_at"]
    assert "request_withdrawn" in [n["type"] for n in api.notifications(mentor)]


def test_withdraw_frees_a_request_slot(api):
    """Withdrawing frees one of the 3 pending-request slots
    Stories: US-12, US-16"""
    student = api.register("student")
    requests = [api.send_request(student, api.mentor(label=f"mentor {n + 1}")) for n in range(3)]
    api._ok(api._raw("post", f"/requests/{requests[0]['id']}/withdraw", student))
    res = api.call("post", "/requests", as_=student, json={"mentor_id": api.mentor(label="mentor 4").id, "personal_message": REQUEST_MESSAGE})
    api.expect(res, 201)


def test_accepted_request_cannot_be_withdrawn(api):
    """An accepted request cannot be withdrawn
    Stories: US-16"""
    student, mentor = api.register("student"), api.mentor()
    request = api.send_request(student, mentor)
    api.decide(mentor, request["id"])
    api.expect(api.call("post", f"/requests/{request['id']}/withdraw", as_=student), 409, body={"detail": "Only pending requests can be withdrawn"})


def test_withdrawn_request_cannot_be_accepted(api):
    """A mentor cannot accept a request the student withdrew
    Stories: US-13, US-16"""
    student, mentor = api.register("student"), api.mentor()
    request = api.send_request(student, mentor)
    api._ok(api._raw("post", f"/requests/{request['id']}/withdraw", student))
    res = api.call("post", f"/requests/{request['id']}/decision", as_=mentor, json={"action": "accept"})
    api.expect(res, 409, body={"detail": "Request is withdrawn"})


def test_student_cannot_withdraw_someone_elses_request(api):
    """A student cannot withdraw another student's request
    Stories: US-16"""
    request = api.send_request(api.register("student"), api.mentor())
    res = api.call("post", f"/requests/{request['id']}/withdraw", as_=api.register("student", label="student B"))
    api.expect(res, 404, body={"detail": "Request not found"})


def test_mentor_cannot_withdraw(api):
    """A mentor cannot use withdraw
    Stories: US-16"""
    mentor = api.mentor()
    request = api.send_request(api.register("student"), mentor)
    api.expect(api.call("post", f"/requests/{request['id']}/withdraw", as_=mentor), 403, body={"detail": "Student access required"})
