"""Mentor endpoints: /mentors/apply, /mentors/me/profile (GET, PUT), /mentors/search, /mentors/{mentor_id}."""

import time

import pytest

from app.models import MentorProfile, User

PROFILE = {
    "career_history": "Analyst at Infosys (2 years), now Data Scientist at Flipkart",
    "organisations": "Infosys, Flipkart",
    "roles": "Data Scientist",
    "years_of_experience": 3,
    "graduation_year": 2023,
    "experience_level": "Experienced",
    "guidance_types": "Job, Higher Studies",
    "preferred_languages": "English, Tamil",
    "max_mentee_capacity": 3,
    "availability": "Weekday evenings",
    "pause_status": "active",
    "expertise_area_ids": [],
}


# ------------------------------------------------------------------ POST /mentors/apply


def test_apply_as_mentor_with_roll_number_year_and_linkedin(api):
    """A graduate applies as a mentor with roll number, graduation year and LinkedIn URL
    Stories: US-02"""
    mentor = api.register("mentor")
    body = {"roll_number": "21f1000123", "graduation_year": 2025, "linked_in_url": "https://www.linkedin.com/in/ravi-kumar"}
    res = api.call("post", "/mentors/apply", as_=mentor, json=body)
    api.expect(res, 201, contains={**body, "status": "pending", "user_id": mentor.id, "admin_decision": None})


def test_apply_twice_is_rejected(api):
    """A mentor cannot submit a second application
    Stories: US-02"""
    mentor = api.register("mentor")
    api.apply(mentor)
    res = api.call("post", "/mentors/apply", as_=mentor, json={"roll_number": "21f1000999"})
    api.expect(res, 400, body={"detail": "Application already submitted"})


def test_apply_forbidden_for_student(api):
    """A student cannot apply through the mentor application endpoint
    Stories: US-02"""
    res = api.call("post", "/mentors/apply", as_=api.register("student"), json={"roll_number": "21f1000001"})
    api.expect(res, 403, body={"detail": "Mentor role required"})


@pytest.mark.parametrize("year", [1949, 2101])
def test_apply_rejects_impossible_graduation_year(api, year):
    """An application with an impossible graduation year is rejected
    Stories: US-02"""
    res = api.call("post", "/mentors/apply", as_=api.register("mentor"), json={"graduation_year": year})
    api.expect(res, 422)


def test_apply_requires_login(api):
    """A mentor application cannot be sent without logging in
    Stories: US-02"""
    api.expect(api.call("post", "/mentors/apply", json={"roll_number": "21f1000001"}), 401)


@pytest.mark.xfail(strict=True, reason="US-02 requires roll number, graduation year and LinkedIn URL, but all three are optional: an empty application is accepted.")
def test_apply_requires_verification_details(api):
    """An application without roll number, graduation year or LinkedIn should be rejected
    Stories: US-02"""
    api.expect(api.call("post", "/mentors/apply", as_=api.register("mentor"), json={}), 422)


# ------------------------------------------------------------------ GET /mentors/me/profile


def test_get_mentor_profile_after_approval(api):
    """An approved mentor reads their profile and current mentee count
    Stories: US-07, US-08"""
    mentor = api.mentor(capacity=2)
    res = api.call("get", "/mentors/me/profile", as_=mentor)
    api.expect(res, 200, contains={"user_id": mentor.id, "status": "approved", "max_mentee_capacity": 2, "current_mentee_count": 0})


def test_get_mentor_profile_counts_active_mentees(api):
    """The mentee count goes up when a request is accepted
    Stories: US-08, US-15"""
    mentor = api.mentor(capacity=3)
    api.relationship(api.register("student"), mentor)
    api.expect(api.call("get", "/mentors/me/profile", as_=mentor), 200, contains={"current_mentee_count": 1})


def test_get_mentor_profile_before_it_exists(api):
    """A mentor who has not been approved or set up a profile gets 404
    Stories: US-07"""
    api.expect(api.call("get", "/mentors/me/profile", as_=api.register("mentor")), 404, body={"detail": "Mentor profile not found"})


def test_get_mentor_profile_forbidden_for_student(api):
    """A student cannot use the mentor profile endpoint
    Stories: US-07"""
    api.expect(api.call("get", "/mentors/me/profile", as_=api.register("student")), 403, body={"detail": "Mentor access required"})


# ------------------------------------------------------------------ PUT /mentors/me/profile


def test_update_mentor_profile_career_path_and_expertise(api):
    """A mentor saves career path, expertise and guidance types
    Stories: US-07"""
    mentor = api.mentor()
    expertise = [api.interest("Data Science"), api.interest("Machine Learning")]
    res = api.call("put", "/mentors/me/profile", as_=mentor, json={**PROFILE, "expertise_area_ids": expertise})
    api.expect(res, 200, contains={**PROFILE, "expertise_area_ids": expertise, "status": "approved"})


@pytest.mark.parametrize("capacity", [1, 5], ids=["min-1", "max-5"])
def test_mentor_capacity_bounds_accepted(api, capacity):
    """Mentee capacity of 1 and 5 is accepted
    Stories: US-08"""
    res = api.call("put", "/mentors/me/profile", as_=api.mentor(), json={**PROFILE, "max_mentee_capacity": capacity})
    api.expect(res, 200, contains={"max_mentee_capacity": capacity})


@pytest.mark.parametrize("capacity", [0, 6], ids=["zero", "six"])
def test_mentor_capacity_out_of_range_rejected(api, capacity):
    """Mentee capacity of 0 or 6 is rejected
    Stories: US-08"""
    res = api.call("put", "/mentors/me/profile", as_=api.mentor(), json={**PROFILE, "max_mentee_capacity": capacity})
    api.expect(res, 422)


def test_mentor_profile_rejects_negative_experience(api):
    """Negative years of experience are rejected
    Stories: US-07"""
    res = api.call("put", "/mentors/me/profile", as_=api.mentor(), json={**PROFILE, "years_of_experience": -1})
    api.expect(res, 422)


def test_mentor_can_pause(api):
    """A mentor pauses and disappears from search
    Stories: US-08, US-09"""
    mentor = api.mentor(name="Paused Mentor")
    res = api.call("put", "/mentors/me/profile", as_=mentor, json={**PROFILE, "pause_status": "paused"})
    api.expect(res, 200, contains={"pause_status": "paused"})
    assert api._raw("get", "/mentors/search", params={"query": "Paused Mentor"}).json()["total"] == 0


def test_mentor_profile_update_forbidden_for_student(api):
    """A student cannot update a mentor profile
    Stories: US-07"""
    api.expect(api.call("put", "/mentors/me/profile", as_=api.register("student"), json=PROFILE), 403)


@pytest.mark.xfail(strict=True, reason="pause_status is not validated by the schema; an unknown value hits the database CHECK constraint and returns 500 instead of 422.")
def test_mentor_profile_rejects_unknown_pause_status(api):
    """An unknown pause status should be rejected with 422
    Stories: US-08"""
    res = api.call("put", "/mentors/me/profile", as_=api.mentor(), json={**PROFILE, "pause_status": "holiday"})
    api.expect(res, 422)


@pytest.mark.xfail(strict=True, reason="experience_level is not validated by the schema; an unknown value hits the database CHECK constraint and returns 500 instead of 422.")
def test_mentor_profile_rejects_unknown_experience_level(api):
    """An unknown experience level should be rejected with 422
    Stories: US-07"""
    res = api.call("put", "/mentors/me/profile", as_=api.mentor(), json={**PROFILE, "experience_level": "Guru"})
    api.expect(res, 422)


# ------------------------------------------------------------------ GET /mentors/search


def _searchable(api):
    """Three approved mentors with different profiles."""
    api.mentor(name="Anita Data", organisations="Google", guidance_types="Job", preferred_languages="English, Hindi", graduation_year=2022, experience_level="Senior", roles="Data Scientist")
    api.mentor(name="Bala Research", organisations="IISc", guidance_types="Research, Higher Studies", preferred_languages="Tamil", graduation_year=2024, experience_level="Recent Graduate", roles="PhD Scholar")
    api.mentor(name="Chitra Startup", organisations="Own startup", guidance_types="Entrepreneurship", preferred_languages="English", graduation_year=2022, experience_level="Experienced", roles="Founder")


@pytest.mark.parametrize(
    "params,expected",
    [
        ({}, ["Anita Data", "Bala Research", "Chitra Startup"]),
        ({"query": "founder"}, ["Chitra Startup"]),
        ({"query": "bala"}, ["Bala Research"]),
        ({"domain": "google"}, ["Anita Data"]),
        ({"industry": "startup"}, ["Chitra Startup"]),
        ({"guidance_type": "higher studies"}, ["Bala Research"]),
        ({"language": "english"}, ["Anita Data", "Chitra Startup"]),
        ({"graduation_year": 2022}, ["Anita Data", "Chitra Startup"]),
        ({"experience_level": "Senior"}, ["Anita Data"]),
        ({"language": "english", "guidance_type": "job"}, ["Anita Data"]),
        ({"query": "nobody-matches"}, []),
    ],
    ids=["no-filter", "by-role", "by-name", "by-domain", "by-industry", "by-guidance", "by-language", "by-year", "by-level", "combined", "no-match"],
)
def test_search_filters(api, params, expected):
    """Mentor search filters by domain, guidance type, industry, graduation year and language
    Stories: US-09"""
    _searchable(api)
    body = api.expect(api.call("get", "/mentors/search", params=params), 200, contains={"total": len(expected)})
    assert [item["name"] for item in body["items"]] == expected


def test_search_hides_unapproved_paused_and_full_mentors(api):
    """Search shows only approved, active mentors with free capacity
    Stories: US-08, US-09"""
    api.register("mentor", name="Zed Unapproved")
    api.mentor(name="Zed Paused", pause_status="paused")
    full = api.mentor(name="Zed Full", capacity=1)
    api.relationship(api.register("student"), full)
    api.mentor(name="Zed Open")
    body = api.expect(api.call("get", "/mentors/search", params={"query": "Zed"}), 200, contains={"total": 1})
    assert body["items"][0]["name"] == "Zed Open"


def test_search_hides_suspended_mentor(api):
    """A suspended mentor does not appear in search
    Stories: US-09, US-24"""
    mentor = api.mentor(name="Suspended Sam")
    api.suspend(mentor)
    api.expect(api.call("get", "/mentors/search", params={"query": "Suspended Sam"}), 200, contains={"total": 0})


def test_search_pagination(api):
    """Search returns results page by page
    Stories: US-09"""
    _searchable(api)
    body = api.expect(api.call("get", "/mentors/search", params={"page": 2, "page_size": 2}), 200, contains={"page": 2, "page_size": 2, "total": 3})
    assert [item["name"] for item in body["items"]] == ["Chitra Startup"]


@pytest.mark.parametrize("params", [{"page": 0}, {"page_size": 0}, {"page_size": 51}], ids=["page-0", "page-size-0", "page-size-51"])
def test_search_rejects_bad_paging(api, params):
    """Search rejects page 0 and page sizes outside 1-50
    Stories: US-09"""
    api.expect(api.call("get", "/mentors/search", params=params), 422)


def test_search_result_hides_contact_details(api):
    """Search results do not show email addresses
    Stories: US-11"""
    mentor = api.mentor(name="Private Priya")
    res = api.call("get", "/mentors/search", params={"query": "Private"})
    api.expect(res, 200, contains={"total": 1})
    assert mentor.email not in res.text and "institute_email" not in res.text


def test_search_responds_within_two_seconds(api):
    """Search over 200 mentors with filters answers in under 2 seconds
    Stories: US-09"""
    from app.api.v1.endpoints.auth import get_password_hash
    from app.db.session import SessionLocal

    password_hash = get_password_hash("password123")
    with SessionLocal() as db:
        for n in range(200):
            user = User(name=f"Bulk Mentor {n:03}", institute_email=f"bulk{n}@study.iitm.ac.in", password_hash=password_hash, role="mentor", account_status="active")
            db.add(user)
            db.flush()
            db.add(MentorProfile(user_id=user.id, status="approved", organisations="TCS" if n % 2 else "Wipro", guidance_types="Job", preferred_languages="English", max_mentee_capacity=3))
        db.commit()
    started = time.perf_counter()
    res = api.call("get", "/mentors/search", params={"domain": "TCS", "language": "English", "page_size": 50})
    elapsed = time.perf_counter() - started
    api.expect(res, 200, contains={"total": 100}, note="response time under 2 seconds")
    assert elapsed < 2, f"search took {elapsed:.2f}s"


@pytest.mark.xfail(strict=True, reason="Mentor search is public: it works without logging in, although US-01 limits the platform to verified students.")
def test_search_requires_login(api):
    """Mentor search should require a logged-in user
    Stories: US-01, US-09"""
    api.mentor()
    api.expect(api.call("get", "/mentors/search"), 401)


# ------------------------------------------------------------------ GET /mentors/{mentor_id}


def test_public_profile_of_approved_mentor(api):
    """A student views an approved mentor's public profile
    Stories: US-11"""
    mentor = api.mentor(name="Deepa Nair", **{k: v for k, v in PROFILE.items() if k not in {"expertise_area_ids", "max_mentee_capacity", "pause_status"}})
    profile_id = api._raw("get", "/mentors/me/profile", mentor).json()["id"]
    res = api.call("get", f"/mentors/{profile_id}", as_=api.register("student"))
    api.expect(res, 200, contains={"id": profile_id, "name": "Deepa Nair", "organisations": "Infosys, Flipkart", "roles": "Data Scientist"})


def test_public_profile_hides_email_and_phone(api):
    """The public mentor profile does not show email or phone
    Stories: US-11"""
    mentor = api.mentor()
    profile_id = api._raw("get", "/mentors/me/profile", mentor).json()["id"]
    res = api.call("get", f"/mentors/{profile_id}")
    body = api.expect(res, 200)
    assert mentor.email not in res.text
    assert not {"institute_email", "email", "phone", "user_id"} & set(body)


def test_public_profile_of_unknown_mentor(api):
    """A mentor id that does not exist returns 404
    Stories: US-11"""
    api.expect(api.call("get", "/mentors/9999"), 404, body={"detail": "Mentor not found"})


def test_public_profile_of_unapproved_mentor(api):
    """An unapproved mentor's profile is not public
    Stories: US-03, US-11"""
    mentor = api.register("mentor")
    profile_id = api._raw("put", "/mentors/me/profile", mentor, json=PROFILE).json()["id"]
    api.expect(api.call("get", f"/mentors/{profile_id}"), 404, body={"detail": "Mentor not found"})


@pytest.mark.xfail(strict=True, reason="The public profile only checks the profile is approved, not that the user is active, so a suspended mentor's profile stays visible.")
def test_public_profile_hidden_after_suspension(api):
    """A suspended mentor's public profile should no longer be shown
    Stories: US-11, US-24"""
    mentor = api.mentor()
    profile_id = api._raw("get", "/mentors/me/profile", mentor).json()["id"]
    api.suspend(mentor)
    api.expect(api.call("get", f"/mentors/{profile_id}"), 404)
