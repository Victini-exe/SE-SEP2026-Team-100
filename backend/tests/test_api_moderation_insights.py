"""Safety, admin insights and notifications.

POST /reports, GET /admin/reports, POST /admin/reports/{id}/review,
POST /admin/users/{id}/suspend, POST /admin/users/{id}/reactivate,
GET /admin/alerts, GET /admin/analytics,
GET /notifications, POST /notifications/{id}/read.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.models import AuditLog, MentoringRelationship, MentoringRequest

DESCRIPTION = "Sent repeated promotional messages about a paid course after I declined."


def _report(api, reporter, target, category="SPAM"):
    return api._ok(api._raw("post", "/reports", reporter, json={"target_user_id": target.id, "category": category, "description": DESCRIPTION}), 201)


# ------------------------------------------------------------------ POST /reports


def test_student_reports_mentor_and_admins_are_told(api):
    """A student reports a mentor; every active admin gets a notification
    Stories: US-23"""
    admin = api.admin()
    student, mentor = api.register("student"), api.mentor()
    payload = {"target_user_id": mentor.id, "category": "HARASSMENT", "description": DESCRIPTION}
    api.expect(api.call("post", "/reports", as_=student, json=payload), 201, contains={"status": "open"})
    assert [n["type"] for n in api.notifications(admin)] == ["new_report"]


def test_mentor_can_report_student(api):
    """A mentor can report a student
    Stories: US-23"""
    student, mentor = api.register("student"), api.mentor()
    payload = {"target_user_id": student.id, "category": "INAPPROPRIATE_BEHAVIOUR", "description": DESCRIPTION}
    api.expect(api.call("post", "/reports", as_=mentor, json=payload), 201, contains={"status": "open"})


@pytest.mark.parametrize(
    "change",
    [{"category": "RUDE"}, {"description": "too short"}, {"description": "x" * 4001}, {"description": " " * 15 + "short"}, {"target_user_id": 0}],
    ids=["unknown-category", "description-9-chars", "description-4001-chars", "description-mostly-spaces", "target-id-0"],
)
def test_report_validation(api, change):
    """Unknown categories and descriptions under 20 or over 4,000 characters are rejected
    Stories: US-23"""
    student, mentor = api.register("student"), api.mentor()
    payload = {"target_user_id": mentor.id, "category": "SPAM", "description": DESCRIPTION, **change}
    api.expect(api.call("post", "/reports", as_=student, json=payload), 422)


def test_cannot_report_yourself(api):
    """A user cannot report themselves
    Stories: US-23"""
    student = api.register("student")
    payload = {"target_user_id": student.id, "category": "SPAM", "description": DESCRIPTION}
    api.expect(api.call("post", "/reports", as_=student, json=payload), 422, body={"detail": "You cannot report yourself"})


def test_cannot_report_unknown_user(api):
    """Reporting a user that does not exist returns 404
    Stories: US-23"""
    payload = {"target_user_id": 9999, "category": "SPAM", "description": DESCRIPTION}
    api.expect(api.call("post", "/reports", as_=api.register("student"), json=payload), 404, body={"detail": "Reported user not found"})


def test_duplicate_open_report_is_refused(api):
    """A second report while the first is still open is refused
    Stories: US-23"""
    student, mentor = api.register("student"), api.mentor()
    _report(api, student, mentor)
    payload = {"target_user_id": mentor.id, "category": "HARASSMENT", "description": DESCRIPTION}
    api.expect(api.call("post", "/reports", as_=student, json=payload), 409, body={"detail": "An unresolved report for this user already exists"})


def test_admin_cannot_file_report(api):
    """Administrators do not file reports themselves
    Stories: US-23"""
    payload = {"target_user_id": api.register("student").id, "category": "SPAM", "description": DESCRIPTION}
    api.expect(api.call("post", "/reports", as_=api.admin(), json=payload), 403, body={"detail": "Only students and mentors may submit reports"})


# ------------------------------------------------------------------ GET /admin/reports


def test_admin_lists_reports(api):
    """An admin lists reports with category, description and status
    Stories: US-24"""
    student, mentor = api.register("student"), api.mentor()
    report = _report(api, student, mentor)
    body = api.expect(api.call("get", "/admin/reports", as_=api.admin()), 200)
    assert body["items"][0] == {**body["items"][0], "id": report["id"], "reporter_id": student.id, "target_user_id": mentor.id, "category": "spam", "description": DESCRIPTION, "status": "open"}


def test_student_cannot_list_reports(api):
    """A student cannot list reports
    Stories: US-24"""
    api.expect(api.call("get", "/admin/reports", as_=api.register("student")), 403, body={"detail": "Admin access required"})


# ------------------------------------------------------------------ POST /admin/reports/{id}/review


@pytest.mark.parametrize("status", ["under_review", "resolved", "dismissed"])
def test_admin_reviews_report(api, status):
    """An admin moves a report to under review, resolved or dismissed with notes, and it is audited
    Stories: US-24"""
    report = _report(api, api.register("student"), api.mentor())
    payload = {"status": status, "admin_review_notes": "Checked message history with both users."}
    api.expect(api.call("post", f"/admin/reports/{report['id']}/review", as_=api.admin(), json=payload), 200, body={"id": report["id"], "status": status})
    assert [a.details for a in api.fetch(AuditLog, action="report_reviewed")] == [f"status={status}"]


def test_resolved_report_cannot_be_reviewed_again(api):
    """A resolved report is final
    Stories: US-24"""
    report = _report(api, api.register("student"), api.mentor())
    api._ok(api._raw("post", f"/admin/reports/{report['id']}/review", api.admin(), json={"status": "resolved", "admin_review_notes": "Warned the user."}))
    res = api.call("post", f"/admin/reports/{report['id']}/review", as_=api.admin(), json={"status": "dismissed", "admin_review_notes": "Second look."})
    api.expect(res, 409, body={"detail": "Report has already been resolved"})


@pytest.mark.parametrize("payload", [{"status": "closed", "admin_review_notes": "Valid notes"}, {"status": "resolved", "admin_review_notes": "ok"}], ids=["unknown-status", "notes-2-chars"])
def test_report_review_validation(api, payload):
    """Unknown statuses and notes under 5 characters are rejected
    Stories: US-24"""
    report = _report(api, api.register("student"), api.mentor())
    api.expect(api.call("post", f"/admin/reports/{report['id']}/review", as_=api.admin(), json=payload), 422)


def test_review_unknown_report(api):
    """Reviewing a report that does not exist returns 404
    Stories: US-24"""
    res = api.call("post", "/admin/reports/9999/review", as_=api.admin(), json={"status": "resolved", "admin_review_notes": "Nothing here."})
    api.expect(res, 404, body={"detail": "Report not found"})


def test_mentor_cannot_review_report(api):
    """A mentor cannot review reports
    Stories: US-24"""
    student, mentor = api.register("student"), api.mentor()
    report = _report(api, mentor, student)
    res = api.call("post", f"/admin/reports/{report['id']}/review", as_=mentor, json={"status": "dismissed", "admin_review_notes": "Not a problem."})
    api.expect(res, 403, body={"detail": "Admin access required"})


# ------------------------------------------------------------------ POST /admin/users/{id}/suspend and /reactivate


def test_suspend_user_pauses_relationships_and_is_audited(api):
    """Suspending a mentor blocks the account, pauses their relationships and records the reason
    Stories: US-24"""
    student, mentor = api.register("student"), api.mentor()
    relationship_id = api.relationship(student, mentor)
    reason = "Confirmed harassment after reviewing the report."
    res = api.call("post", f"/admin/users/{mentor.id}/suspend", as_=api.admin(), json={"reason": reason})
    api.expect(res, 200, body={"id": mentor.id, "account_status": "suspended", "suspended_relationships": 1})
    assert api.fetch(MentoringRelationship, id=relationship_id)[0].status == "suspended"
    assert [a.details for a in api.fetch(AuditLog, action="account_suspended")] == [reason]
    assert api._raw("get", "/relationships", mentor).status_code == 403


def test_message_to_suspended_user_is_refused(api):
    """No messages can be sent in a relationship paused by suspension
    Stories: US-19, US-24"""
    student, mentor = api.register("student"), api.mentor()
    relationship_id = api.relationship(student, mentor)
    api.suspend(mentor)
    res = api.call("post", f"/relationships/{relationship_id}/messages", as_=student, json={"content": "Are you there?"})
    api.expect(res, 409, body={"detail": "Relationship is not active"})


def test_reactivate_restores_account_and_relationship(api):
    """Reactivating restores the account and resumes its relationships
    Stories: US-24"""
    student, mentor = api.register("student"), api.mentor()
    relationship_id = api.relationship(student, mentor)
    api.suspend(mentor)
    reason = "Appeal accepted after review of evidence."
    res = api.call("post", f"/admin/users/{mentor.id}/reactivate", as_=api.admin(), json={"reason": reason})
    api.expect(res, 200, body={"id": mentor.id, "account_status": "active"})
    assert api.fetch(MentoringRelationship, id=relationship_id)[0].status == "active"
    assert [a.details for a in api.fetch(AuditLog, action="account_reactivated")] == [reason]


def test_reactivate_returns_pending_mentor_to_pending(api):
    """A suspended mentor who was still unverified goes back to pending verification
    Stories: US-03, US-24"""
    mentor = api.register("mentor")
    api.suspend(mentor)
    res = api.call("post", f"/admin/users/{mentor.id}/reactivate", as_=api.admin(), json={"reason": "Suspended by mistake, restoring."})
    api.expect(res, 200, body={"id": mentor.id, "account_status": "pending_verification"})


def test_relationship_stays_paused_while_other_side_suspended(api):
    """A relationship resumes only when neither side is suspended
    Stories: US-24"""
    student, mentor = api.register("student"), api.mentor()
    relationship_id = api.relationship(student, mentor)
    api.suspend(mentor)
    api.suspend(student)
    api.expect(api.call("post", f"/admin/users/{mentor.id}/reactivate", as_=api.admin(), json={"reason": "Mentor appeal accepted."}), 200)
    assert api.fetch(MentoringRelationship, id=relationship_id)[0].status == "suspended"


@pytest.mark.parametrize(
    "case,detail",
    [("self", "Administrators cannot suspend their own account"), ("twice", "User is already suspended"), ("unknown", "User not found")],
)
def test_suspend_refusals(api, case, detail):
    """Admins cannot suspend themselves, suspend twice, or suspend unknown users
    Stories: US-24"""
    admin = api.admin()
    student = api.register("student")
    target = {"self": admin.id, "twice": student.id, "unknown": 9999}[case]
    if case == "twice":
        api.suspend(student)
    status = 404 if case == "unknown" else 409
    res = api.call("post", f"/admin/users/{target}/suspend", as_=admin, json={"reason": "Testing suspension rules."})
    api.expect(res, status, body={"detail": detail})


def test_suspend_requires_reason(api):
    """A suspension reason under 10 real characters is rejected
    Stories: US-24"""
    student = api.register("student")
    api.expect(api.call("post", f"/admin/users/{student.id}/suspend", as_=api.admin(), json={"reason": "   spam    "}), 422)


def test_reactivate_active_user_is_refused(api):
    """Reactivating a user who is not suspended is refused
    Stories: US-24"""
    student = api.register("student")
    res = api.call("post", f"/admin/users/{student.id}/reactivate", as_=api.admin(), json={"reason": "Nothing to reactivate."})
    api.expect(res, 409, body={"detail": "User is not suspended"})


def test_student_cannot_suspend(api):
    """A student cannot suspend another user
    Stories: US-24"""
    other = api.register("student", label="student B")
    res = api.call("post", f"/admin/users/{other.id}/suspend", as_=api.register("student"), json={"reason": "I do not like them."})
    api.expect(res, 403, body={"detail": "Admin access required"})


# ------------------------------------------------------------------ GET /admin/alerts


def test_alerts_list_stale_requests_and_inactive_relationships(api):
    """Admins see requests pending over 5 days and relationships idle for 30 days
    Stories: US-22"""
    now = datetime.now(timezone.utc)
    mentor = api.mentor(capacity=3)
    stale = api.send_request(api.register("student"), mentor)
    fresh = api.send_request(api.register("student", label="student B"), mentor)
    api.update_row(MentoringRequest, stale["id"], created_at=now - timedelta(days=6))
    idle = api.relationship(api.register("student", label="student C"), mentor)
    api.update_row(MentoringRelationship, idle, last_activity_at=now - timedelta(days=31))
    body = api.expect(api.call("get", "/admin/alerts", as_=api.admin()), 200)
    assert [r["id"] for r in body["stale_requests"]] == [stale["id"]]
    assert fresh["id"] not in [r["id"] for r in body["stale_requests"]]
    assert [r["id"] for r in body["inactive_relationships"]] == [idle]


def test_alerts_empty_when_everything_is_recent(api):
    """No alerts when every request and relationship is recent
    Stories: US-22"""
    student, mentor = api.register("student"), api.mentor()
    api.relationship(student, mentor)
    api.expect(api.call("get", "/admin/alerts", as_=api.admin()), 200, body={"stale_requests": [], "inactive_relationships": []})


def test_alerts_forbidden_for_mentor(api):
    """A mentor cannot see admin alerts
    Stories: US-22"""
    api.expect(api.call("get", "/admin/alerts", as_=api.mentor()), 403, body={"detail": "Admin access required"})


# ------------------------------------------------------------------ GET /admin/analytics


def test_analytics_counts_participation(api):
    """Analytics count active mentors and mentees, requests, acceptance rate and sessions
    Stories: US-21"""
    mentor = api.mentor(capacity=3)
    api.mentor(label="mentor B")
    relationship_id = api.relationship(api.register("student"), mentor)
    api.send_request(api.register("student", label="student B"), mentor)
    api.session(relationship_id, mentor, datetime.now(timezone.utc) + timedelta(days=1))
    body = api.expect(api.call("get", "/admin/analytics", as_=api.admin()), 200)
    assert body == {
        **body,
        "active_mentors": 2,
        "active_mentees": 1,
        "active_relationships": 1,
        "requests": 2,
        "accepted_requests": 1,
        "acceptance_rate": 0.5,
        "sessions": 1,
    }
    assert body["participation_trends"][0]["relationships_started"] == 1


def test_analytics_hide_groups_smaller_than_three(api):
    """Career goals shared by fewer than 3 students are hidden for privacy
    Stories: US-21"""
    for n in range(3):
        api.student(label=f"student {n}", career_goal="Job")
    for n in range(2):
        api.student(label=f"student R{n}", career_goal="Research")
    body = api.expect(api.call("get", "/admin/analytics", as_=api.admin()), 200)
    assert body["career_goals"] == [{"goal": "Job", "count": 3}]


def test_analytics_flags_domains_with_little_capacity(api):
    """Domains with fewer than 3 free mentor slots are flagged
    Stories: US-21"""
    api.mentor(organisations="Healthcare", capacity=1)
    api.mentor(organisations="Finance", capacity=5)
    body = api.expect(api.call("get", "/admin/analytics", as_=api.admin()), 200)
    assert body["insufficient_mentor_availability"] == [{"domain": "Healthcare", "available_capacity": 1}]


def test_analytics_filtered_by_date_range(api):
    """Analytics can be limited to a date range
    Stories: US-21"""
    mentor = api.mentor(capacity=3)
    old = api.send_request(api.register("student"), mentor)
    api.update_row(MentoringRequest, old["id"], created_at=datetime(2026, 1, 15, tzinfo=timezone.utc))
    api.send_request(api.register("student", label="student B"), mentor)
    params = {"start": "2026-01-01T00:00:00Z", "end": "2026-01-31T23:59:59Z"}
    api.expect(api.call("get", "/admin/analytics", as_=api.admin(), params=params), 200, contains={"requests": 1})


def test_analytics_start_after_end_is_rejected(api):
    """A start date after the end date is rejected
    Stories: US-21"""
    params = {"start": "2026-02-01T00:00:00Z", "end": "2026-01-01T00:00:00Z"}
    api.expect(api.call("get", "/admin/analytics", as_=api.admin(), params=params), 422, body={"detail": "Start must not be after end"})


def test_analytics_forbidden_for_student(api):
    """A student cannot see analytics
    Stories: US-21"""
    api.expect(api.call("get", "/admin/analytics", as_=api.register("student")), 403, body={"detail": "Admin access required"})


# ------------------------------------------------------------------ GET /notifications, POST /notifications/{id}/read


def test_user_lists_own_notifications_newest_first(api):
    """A user sees their own notifications, newest first
    Stories: US-13, US-14"""
    student, mentor = api.register("student"), api.mentor()
    request = api.send_request(student, mentor)
    api.decide(mentor, request["id"], "decline")
    body = api.expect(api.call("get", "/notifications", as_=student), 200)
    assert [n["type"] for n in body["items"]] == ["request_declined"]
    assert body["items"][0]["is_read"] is False and body["items"][0]["entity_id"] == request["id"]


def test_mark_notification_read(api):
    """A user marks a notification as read
    Stories: US-14"""
    student, mentor = api.register("student"), api.mentor()
    api.send_request(student, mentor)
    note = api.notifications(mentor)[0]
    api.expect(api.call("post", f"/notifications/{note['id']}/read", as_=mentor), 200, body={"id": note["id"], "is_read": True})
    assert api.notifications(mentor)[0]["is_read"] is True


def test_cannot_mark_someone_elses_notification(api):
    """A user cannot mark another user's notification
    Stories: US-14"""
    student, mentor = api.register("student"), api.mentor()
    api.send_request(student, mentor)
    note = api.notifications(mentor)[0]
    api.expect(api.call("post", f"/notifications/{note['id']}/read", as_=student), 404, body={"detail": "Notification not found"})


def test_notifications_require_login(api):
    """Notifications cannot be read without logging in
    Stories: US-14"""
    api.expect(api.call("get", "/notifications"), 401)
