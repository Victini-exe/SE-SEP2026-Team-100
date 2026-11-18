"""Admin endpoints: /admin/dashboard, /admin/users, /admin/applications, /admin/applications/{id}/review."""

import pytest

from app.models import MentorProfile


# ------------------------------------------------------------------ GET /admin/applications


def test_list_applications_shows_pending_application(api):
    """An admin sees a submitted mentor application with its details
    Stories: US-03"""
    mentor = api.register("mentor")
    application = api.apply(mentor, roll_number="21f2000456", graduation_year=2024)
    body = api.expect(api.call("get", "/admin/applications", as_=api.admin()), 200)
    assert [item["id"] for item in body] == [application["id"]]
    assert body[0]["status"] == "pending" and body[0]["roll_number"] == "21f2000456"


def test_list_applications_forbidden_for_mentor(api):
    """A mentor cannot list mentor applications
    Stories: US-03"""
    api.expect(api.call("get", "/admin/applications", as_=api.register("mentor")), 403, body={"detail": "Admin access required"})


def test_list_applications_requires_login(api):
    """Mentor applications cannot be listed without logging in
    Stories: US-03"""
    api.expect(api.call("get", "/admin/applications"), 401)


# ------------------------------------------------------------------ POST /admin/applications/{id}/review


def test_approve_application_activates_mentor(api):
    """Approving an application activates the mentor account and profile
    Stories: US-03"""
    mentor = api.register("mentor")
    application = api.apply(mentor)
    res = api.call("post", f"/admin/applications/{application['id']}/review", as_=api.admin(), json={"action": "approve"})
    body = api.expect(res, 200, contains={"id": application["id"], "status": "approved"})
    assert body["decision_at"]
    assert api._raw("get", "/auth/me", mentor).json()["account_status"] == "active"
    assert api.fetch(MentorProfile, user_id=mentor.id)[0].status == "approved"


def test_reject_application_with_reason(api):
    """Rejecting an application records the reason
    Stories: US-03"""
    application = api.apply(api.register("mentor"))
    payload = {"action": "reject", "rejection_reason": "Roll number does not match our graduate records."}
    res = api.call("post", f"/admin/applications/{application['id']}/review", as_=api.admin(), json=payload)
    api.expect(res, 200, contains={"status": "rejected"})
    listed = api._raw("get", "/admin/applications", api.admin()).json()[0]
    assert listed["rejection_reason"] == payload["rejection_reason"] and listed["admin_decision"] == "rejected"


def test_rejected_mentor_stays_unverified(api):
    """A rejected mentor stays pending verification and is not searchable
    Stories: US-03"""
    mentor = api.register("mentor", name="Rejected Raj")
    application = api.apply(mentor)
    payload = {"action": "reject", "rejection_reason": "Could not verify graduation."}
    api.expect(api.call("post", f"/admin/applications/{application['id']}/review", as_=api.admin(), json=payload), 200)
    assert api._raw("get", "/auth/me", mentor).json()["account_status"] == "pending_verification"
    assert api._raw("get", "/mentors/search", params={"query": "Rejected Raj"}).json()["total"] == 0


@pytest.mark.parametrize("reason", [None, "", "no"], ids=["missing", "empty", "under-5-chars"])
def test_reject_requires_reason(api, reason):
    """Rejecting without a reason of at least 5 characters is refused
    Stories: US-03"""
    application = api.apply(api.register("mentor"))
    payload = {"action": "reject", "rejection_reason": reason}
    res = api.call("post", f"/admin/applications/{application['id']}/review", as_=api.admin(), json=payload)
    api.expect(res, 400, body={"detail": "Rejection reason is required"})


def test_review_rejects_unknown_action(api):
    """A review action other than approve or reject is refused
    Stories: US-03"""
    application = api.apply(api.register("mentor"))
    res = api.call("post", f"/admin/applications/{application['id']}/review", as_=api.admin(), json={"action": "maybe"})
    api.expect(res, 422)


def test_review_unknown_application(api):
    """Reviewing an application that does not exist returns 404
    Stories: US-03"""
    res = api.call("post", "/admin/applications/9999/review", as_=api.admin(), json={"action": "approve"})
    api.expect(res, 404, body={"detail": "Application not found"})


def test_review_forbidden_for_student(api):
    """A student cannot review mentor applications
    Stories: US-03"""
    application = api.apply(api.register("mentor"))
    res = api.call("post", f"/admin/applications/{application['id']}/review", as_=api.register("student"), json={"action": "approve"})
    api.expect(res, 403, body={"detail": "Admin access required"})


def test_mentor_cannot_approve_own_application(api):
    """A mentor cannot approve their own application
    Stories: US-03"""
    mentor = api.register("mentor")
    application = api.apply(mentor)
    res = api.call("post", f"/admin/applications/{application['id']}/review", as_=mentor, json={"action": "approve"})
    api.expect(res, 403, body={"detail": "Admin access required"})


@pytest.mark.xfail(strict=True, reason="A decided application can be reviewed again. Rejecting after approval marks it rejected but leaves the mentor profile approved and searchable.")
def test_decided_application_cannot_be_reviewed_again(api):
    """An application that was already approved cannot be reviewed again
    Stories: US-03"""
    application = api.apply(api.register("mentor"))
    api.approve(application["id"])
    payload = {"action": "reject", "rejection_reason": "Changed my mind after approval."}
    res = api.call("post", f"/admin/applications/{application['id']}/review", as_=api.admin(), json=payload)
    api.expect(res, 409)


# ------------------------------------------------------------------ GET /admin/dashboard


def test_dashboard_counts_pending_and_approved(api):
    """The dashboard counts pending applications and approved mentors
    Stories: US-21"""
    api.apply(api.register("mentor"))
    api.apply(api.register("mentor"))
    api.mentor()
    res = api.call("get", "/admin/dashboard", as_=api.admin())
    api.expect(res, 200, body={"pending_applications": 2, "approved_mentors": 1, "recent_activity": []})


def test_dashboard_excludes_suspended_mentors(api):
    """A suspended mentor is not counted as an approved mentor
    Stories: US-21, US-24"""
    api.mentor()
    api.suspend(api.mentor())
    api.expect(api.call("get", "/admin/dashboard", as_=api.admin()), 200, contains={"approved_mentors": 1})


def test_dashboard_forbidden_for_student(api):
    """A student cannot open the admin dashboard
    Stories: US-21"""
    api.expect(api.call("get", "/admin/dashboard", as_=api.register("student")), 403, body={"detail": "Admin access required"})


def test_dashboard_requires_login(api):
    """The admin dashboard cannot be opened without logging in
    Stories: US-21"""
    api.expect(api.call("get", "/admin/dashboard"), 401)


# ------------------------------------------------------------------ GET /admin/users


def test_list_users_with_roles_and_status(api):
    """An admin lists all users with role and account status
    Stories: US-21, US-24"""
    admin = api.admin()
    student, mentor = api.register("student"), api.register("mentor")
    body = api.expect(api.call("get", "/admin/users", as_=admin), 200, contains={"page": 1, "page_size": 50, "total": 3})
    by_id = {item["id"]: item for item in body["items"]}
    assert by_id[student.id]["role"] == "student" and by_id[mentor.id]["account_status"] == "pending_verification"
    assert "institute_email" not in body["items"][0]


def test_list_users_pagination(api):
    """The user list is paged
    Stories: US-21"""
    admin = api.admin()
    for _ in range(3):
        api.register("student")
    body = api.expect(api.call("get", "/admin/users", as_=admin, params={"page": 2, "page_size": 3}), 200, contains={"total": 4, "page": 2})
    assert len(body["items"]) == 1


@pytest.mark.parametrize("params,expected", [({"page": 0}, {"page": 1}), ({"page_size": 1000}, {"page_size": 100}), ({"page_size": 0}, {"page_size": 1})], ids=["page-0", "page-size-1000", "page-size-0"])
def test_list_users_clamps_paging(api, params, expected):
    """Out-of-range paging values are clamped instead of failing
    Stories: US-21"""
    api.expect(api.call("get", "/admin/users", as_=api.admin(), params=params), 200, contains=expected)


def test_list_users_forbidden_for_mentor(api):
    """A mentor cannot list users
    Stories: US-21"""
    api.expect(api.call("get", "/admin/users", as_=api.mentor()), 403, body={"detail": "Admin access required"})
