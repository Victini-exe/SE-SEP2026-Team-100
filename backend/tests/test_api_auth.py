"""Auth endpoints: /auth/register, /auth/login, /auth/login-form, /auth/me, /auth/logout and /health."""

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from api_testkit import PASSWORD
from app.api.v1.endpoints.auth import create_access_token
from app.config import get_settings
from app.models import User


# ------------------------------------------------------------------ POST /auth/register


def test_register_student_with_institute_email(api):
    """A student registers with an IITM BS institute email
    Stories: US-01"""
    email = api.unique_email("student")
    payload = {"name": "Asha Raman", "institute_email": email, "password": PASSWORD, "role": "student"}
    res = api.call("post", "/auth/register", json=payload)
    api.expect(res, 201, contains={"name": "Asha Raman", "institute_email": email, "role": "student", "account_status": "active"})
    assert "password" not in res.text and "password_hash" not in res.text


def test_register_mentor_starts_pending_verification(api):
    """A mentor registration waits for admin verification
    Stories: US-02, US-03"""
    payload = {"name": "Ravi Kumar", "institute_email": api.unique_email("mentor"), "password": PASSWORD, "role": "mentor"}
    res = api.call("post", "/auth/register", json=payload)
    api.expect(res, 201, contains={"role": "mentor", "account_status": "pending_verification"})


def test_register_accepts_second_allowed_domain(api):
    """Registration accepts the other configured domain, iitm.ac.in
    Stories: US-01"""
    payload = {"name": "Staff Student", "institute_email": "someone.new@iitm.ac.in", "password": PASSWORD, "role": "student"}
    api.expect(api.call("post", "/auth/register", json=payload), 201, contains={"institute_email": "someone.new@iitm.ac.in"})


def test_register_stores_email_in_lower_case(api):
    """Registration stores the email in lower case
    Stories: US-01"""
    payload = {"name": "Mixed Case", "institute_email": "Mixed.Case@Study.IITM.ac.in", "password": PASSWORD, "role": "student"}
    api.expect(api.call("post", "/auth/register", json=payload), 201, contains={"institute_email": "mixed.case@study.iitm.ac.in"})


def test_register_rejects_non_institute_email(api):
    """Registration with a Gmail address is rejected
    Stories: US-01"""
    payload = {"name": "Outsider", "institute_email": "outsider@gmail.com", "password": PASSWORD, "role": "student"}
    api.expect(api.call("post", "/auth/register", json=payload), 400, body={"detail": "Institute email domain not allowed"})


def test_register_rejects_lookalike_domain(api):
    """Registration with a look-alike domain (fakestudy.iitm.ac.in) is rejected
    Stories: US-01"""
    payload = {"name": "Spoofer", "institute_email": "x@fakestudy.iitm.ac.in", "password": PASSWORD, "role": "student"}
    api.expect(api.call("post", "/auth/register", json=payload), 400, body={"detail": "Institute email domain not allowed"})


def test_register_rejects_duplicate_email(api):
    """Registering the same email twice is rejected
    Stories: US-01"""
    email = api.unique_email("dup")
    payload = {"name": "First User", "institute_email": email, "password": PASSWORD, "role": "student"}
    api._ok(api._raw("post", "/auth/register", json=payload), 201)
    api.expect(api.call("post", "/auth/register", json=payload), 400, body={"detail": "User already exists"})


def test_register_rejects_duplicate_email_with_different_case(api):
    """An email that differs only in letter case counts as a duplicate
    Stories: US-01"""
    email = api.unique_email("case")
    api._ok(api._raw("post", "/auth/register", json={"name": "Lower", "institute_email": email, "password": PASSWORD}), 201)
    payload = {"name": "Upper", "institute_email": email.upper(), "password": PASSWORD, "role": "student"}
    api.expect(api.call("post", "/auth/register", json=payload), 400, body={"detail": "User already exists"})


def test_register_cannot_create_admin(api):
    """Public registration cannot create an administrator
    Stories: US-03"""
    payload = {"name": "Not Admin", "institute_email": api.unique_email("adm"), "password": PASSWORD, "role": "admin"}
    api.expect(api.call("post", "/auth/register", json=payload), 400, body={"detail": "Only student and mentor registration is available"})


def test_register_role_is_case_insensitive(api):
    """Role 'MENTOR' in capitals is accepted and stored as 'mentor'
    Stories: US-02"""
    payload = {"name": "Caps Mentor", "institute_email": api.unique_email("caps"), "password": PASSWORD, "role": "MENTOR"}
    api.expect(api.call("post", "/auth/register", json=payload), 201, contains={"role": "mentor"})


@pytest.mark.parametrize(
    "field,value",
    [
        ("password", "short7!"),
        ("password", "x" * 129),
        ("name", "A"),
        ("name", "N" * 151),
        ("institute_email", "not-an-email"),
    ],
    ids=["password-7-chars", "password-129-chars", "name-1-char", "name-151-chars", "malformed-email"],
)
def test_register_validates_fields(api, field, value):
    """Registration rejects out-of-range fields with 422
    Stories: US-01"""
    payload = {"name": "Valid Name", "institute_email": api.unique_email("val"), "password": PASSWORD, "role": "student"}
    payload[field] = value
    res = api.call("post", "/auth/register", json=payload)
    api.expect(res, 422)
    assert res.json()["detail"][0]["loc"][-1] == field


def test_register_requires_email(api):
    """Registration without an email is rejected with 422
    Stories: US-01"""
    res = api.call("post", "/auth/register", json={"name": "No Email", "password": PASSWORD})
    api.expect(res, 422)


# ------------------------------------------------------------------ POST /auth/login


def test_login_returns_bearer_token(api):
    """A registered student logs in and receives a bearer token
    Stories: US-01"""
    student = api.register("student")
    res = api.call("post", "/auth/login", json={"institute_email": student.email, "password": PASSWORD})
    body = api.expect(res, 200, contains={"token_type": "bearer"})
    assert body["access_token"].count(".") == 2


def test_login_token_lasts_at_most_24_hours(api):
    """The login token expires within 24 hours
    Stories: US-01"""
    student = api.register("student")
    res = api.call("post", "/auth/login", json={"institute_email": student.email, "password": PASSWORD})
    token = api.expect(res, 200)["access_token"]
    claims = jwt.get_unverified_claims(token)
    lifetime = datetime.fromtimestamp(claims["exp"], timezone.utc) - datetime.now(timezone.utc)
    assert timedelta(0) < lifetime <= timedelta(hours=24)


def test_login_email_is_case_insensitive(api):
    """Login works with the email typed in capitals
    Stories: US-01"""
    student = api.register("student")
    res = api.call("post", "/auth/login", json={"institute_email": student.email.upper(), "password": PASSWORD})
    api.expect(res, 200)


def test_login_records_last_login_time(api):
    """A successful login records the last login time
    Stories: US-01"""
    student = api.register("student")
    api.update_row(User, student.id, last_login_at=None)
    api.expect(api.call("post", "/auth/login", json={"institute_email": student.email, "password": PASSWORD}), 200)
    assert api.fetch(User, id=student.id)[0].last_login_at is not None


def test_login_rejects_wrong_password(api):
    """Login with a wrong password is rejected
    Stories: US-01"""
    student = api.register("student")
    res = api.call("post", "/auth/login", json={"institute_email": student.email, "password": "wrong-password"})
    api.expect(res, 401, body={"detail": "Invalid credentials"})


def test_login_rejects_unknown_email(api):
    """Login with an email that is not registered is rejected
    Stories: US-01"""
    res = api.call("post", "/auth/login", json={"institute_email": "nobody@study.iitm.ac.in", "password": PASSWORD})
    api.expect(res, 401, body={"detail": "Invalid credentials"})


def test_login_blocks_suspended_account(api):
    """A suspended user cannot log in
    Stories: US-24"""
    student = api.register("student")
    api.suspend(student)
    res = api.call("post", "/auth/login", json={"institute_email": student.email, "password": PASSWORD})
    api.expect(res, 403, body={"detail": "Account suspended"})


def test_login_requires_password_field(api):
    """Login without a password field is rejected with 422
    Stories: US-01"""
    api.expect(api.call("post", "/auth/login", json={"institute_email": "a@study.iitm.ac.in"}), 422)


# ------------------------------------------------------------------ POST /auth/login-form


def test_login_form_returns_token(api):
    """The OAuth2 form login (used by Swagger 'Authorize') returns a token
    Stories: US-01"""
    student = api.register("student")
    res = api.call("post", "/auth/login-form", data={"username": student.email, "password": PASSWORD})
    api.expect(res, 200, contains={"token_type": "bearer"})


def test_login_form_rejects_wrong_password(api):
    """The form login rejects a wrong password
    Stories: US-01"""
    student = api.register("student")
    res = api.call("post", "/auth/login-form", data={"username": student.email, "password": "nope-nope"})
    api.expect(res, 401, body={"detail": "Invalid credentials"})


def test_login_form_requires_username(api):
    """The form login without a username is rejected with 422
    Stories: US-01"""
    api.expect(api.call("post", "/auth/login-form", data={"password": PASSWORD}), 422)


# ------------------------------------------------------------------ GET /auth/me


def test_me_returns_current_user(api):
    """/auth/me returns the logged-in user
    Stories: US-01"""
    student = api.register("student", name="Meera Iyer")
    res = api.call("get", "/auth/me", as_=student)
    api.expect(res, 200, body={"id": student.id, "name": "Meera Iyer", "institute_email": student.email, "role": "student", "account_status": "active"})


def test_me_without_token(api):
    """/auth/me without a token is rejected
    Stories: US-01"""
    api.expect(api.call("get", "/auth/me"), 401, body={"detail": "Not authenticated"})


def test_me_with_garbage_token(api):
    """/auth/me with a malformed token is rejected
    Stories: US-01"""
    res = api.call("get", "/auth/me", headers={"Authorization": "Bearer not.a.token"})
    api.expect(res, 401, body={"detail": "Could not validate credentials"})


def test_me_with_expired_token(api):
    """/auth/me with an expired token is rejected
    Stories: US-01"""
    student = api.register("student")
    expired = create_access_token(student.email, expires_delta=timedelta(minutes=-1))
    res = api.call("get", "/auth/me", headers={"Authorization": f"Bearer {expired}"})
    api.expect(res, 401, body={"detail": "Could not validate credentials"})


def test_me_with_token_signed_by_wrong_key(api):
    """/auth/me with a token signed by another key is rejected
    Stories: US-01"""
    student = api.register("student")
    forged = jwt.encode({"sub": student.email, "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, "attacker-key", algorithm=get_settings().algorithm)
    res = api.call("get", "/auth/me", headers={"Authorization": f"Bearer {forged}"})
    api.expect(res, 401, body={"detail": "Could not validate credentials"})


def test_me_with_token_for_unknown_user(api):
    """/auth/me with a valid token for a user that does not exist is rejected
    Stories: US-01"""
    token = create_access_token("ghost@study.iitm.ac.in")
    res = api.call("get", "/auth/me", headers={"Authorization": f"Bearer {token}"})
    api.expect(res, 401, body={"detail": "Could not validate credentials"})


def test_me_rejects_token_of_suspended_user(api):
    """An already-issued token stops working once the user is suspended
    Stories: US-24"""
    student = api.register("student")
    api.suspend(student)
    api.expect(api.call("get", "/auth/me", as_=student), 403, body={"detail": "Account suspended"})


# ------------------------------------------------------------------ POST /auth/logout, GET /health


def test_logout_returns_confirmation(api):
    """Logout returns a confirmation message
    Stories: US-01"""
    api.expect(api.call("post", "/auth/logout"), 200, body={"detail": "Logged out"})


@pytest.mark.xfail(strict=True, reason="Logout does not revoke the token: the old token still works afterwards (JWT is stateless and there is no deny-list).")
def test_logout_invalidates_token(api):
    """After logout the old token should no longer work
    Stories: US-01"""
    student = api.register("student")
    api.call("post", "/auth/logout", as_=student)
    api.expect(api.call("get", "/auth/me", as_=student), 401)


def test_health_check(api):
    """The health check reports the service is up"""
    api.expect(api.call("get", "/health"), 200, body={"status": "ok"})
