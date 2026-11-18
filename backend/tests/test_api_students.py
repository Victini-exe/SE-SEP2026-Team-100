"""Student endpoints: /students/me/profile (GET, PUT) and /students/questions (GET, POST)."""

from datetime import datetime, timedelta, timezone

import pytest

from app.models import CareerQuestion, StudentProfile

PROFILE = {
    "career_goal": "Job",
    "current_situation": "Final-year BS student working part-time",
    "preferred_language": "English",
    "weekly_availability": "Weekends, 2 hours",
    "career_aspirations": "Data scientist in a product company",
    "interest_area_ids": [],
}


# ------------------------------------------------------------------ GET /students/me/profile


def test_get_profile_before_creating_one(api):
    """A new student has no mentoring profile yet
    Stories: US-04"""
    student = api.register("student")
    api.expect(api.call("get", "/students/me/profile", as_=student), 404, body={"detail": "Student profile not found"})


def test_get_profile_returns_saved_profile(api):
    """A student reads back the profile they saved
    Stories: US-04"""
    data_science = api.interest("Data Science")
    student = api.student(**{**PROFILE, "interest_area_ids": [data_science]})
    res = api.call("get", "/students/me/profile", as_=student)
    api.expect(res, 200, contains={**PROFILE, "interest_area_ids": [data_science], "user_id": student.id})


def test_get_profile_forbidden_for_mentor(api):
    """A mentor cannot use the student profile endpoint
    Stories: US-04"""
    mentor = api.register("mentor")
    api.expect(api.call("get", "/students/me/profile", as_=mentor), 403, body={"detail": "Student access required"})


def test_get_profile_requires_login(api):
    """The student profile cannot be read without logging in
    Stories: US-01, US-04"""
    api.expect(api.call("get", "/students/me/profile"), 401)


# ------------------------------------------------------------------ PUT /students/me/profile


def test_create_profile_with_goal_interests_language_availability(api):
    """A student creates a mentoring profile with goal, interests, language and availability
    Stories: US-04"""
    student = api.register("student")
    ids = [api.interest("Data Science"), api.interest("Higher Studies")]
    res = api.call("put", "/students/me/profile", as_=student, json={**PROFILE, "interest_area_ids": ids})
    api.expect(res, 200, contains={**PROFILE, "interest_area_ids": ids})


def test_update_profile_replaces_previous_values(api):
    """Updating the profile replaces the old goal and interests
    Stories: US-06"""
    first, second = api.interest("Data Science"), api.interest("Entrepreneurship")
    student = api.student(**{**PROFILE, "interest_area_ids": [first]})
    update = {**PROFILE, "career_goal": "Entrepreneurship", "interest_area_ids": [second]}
    res = api.call("put", "/students/me/profile", as_=student, json=update)
    api.expect(res, 200, contains={"career_goal": "Entrepreneurship", "interest_area_ids": [second]})


def test_profile_keeps_only_first_five_interests(api):
    """Only the first 5 interest areas are kept
    Stories: US-04
    The student story allows up to 5 interest areas; extra ones are dropped."""
    student = api.register("student")
    ids = [api.interest(f"Area {n}") for n in range(6)]
    res = api.call("put", "/students/me/profile", as_=student, json={**PROFILE, "interest_area_ids": ids})
    body = api.expect(res, 200)
    assert body["interest_area_ids"] == ids[:5]


def test_profile_ignores_unknown_interest_ids(api):
    """Interest ids that do not exist are ignored
    Stories: US-04"""
    student = api.register("student")
    real = api.interest("Research")
    res = api.call("put", "/students/me/profile", as_=student, json={**PROFILE, "interest_area_ids": [real, 9999]})
    api.expect(res, 200, contains={"interest_area_ids": [real]})


@pytest.mark.parametrize(
    "field,limit",
    [("career_goal", 1000), ("current_situation", 1000), ("preferred_language", 100), ("weekly_availability", 1000), ("career_aspirations", 2000)],
)
def test_profile_rejects_overlong_fields(api, field, limit):
    """Profile text longer than its limit is rejected with 422
    Stories: US-04"""
    student = api.register("student")
    res = api.call("put", "/students/me/profile", as_=student, json={**PROFILE, field: "x" * (limit + 1)})
    api.expect(res, 422)


def test_profile_update_forbidden_for_admin(api):
    """An administrator cannot create a student profile
    Stories: US-04"""
    api.expect(api.call("put", "/students/me/profile", as_=api.admin(), json=PROFILE), 403, body={"detail": "Student access required"})


@pytest.mark.xfail(strict=True, reason="US-06 asks for each profile change to be saved with a date; profile_history is never written and no change log exists.")
def test_profile_change_is_saved_with_a_date(api):
    """Each profile change is kept with its date
    Stories: US-06"""
    student = api.student(**PROFILE)
    api.expect(api.call("put", "/students/me/profile", as_=student, json={**PROFILE, "career_goal": "Research"}), 200)
    profile = api.fetch(StudentProfile, user_id=student.id)[0]
    assert profile.profile_history, "no history of profile changes was stored"


# ------------------------------------------------------------------ POST /students/questions


def test_create_career_question(api):
    """A student adds a career question (50-500 characters)
    Stories: US-05"""
    student = api.register("student")
    text = "How should I prepare for data science interviews in my final term of the BS degree?"
    res = api.call("post", "/students/questions", as_=student, json={"question_text": text})
    body = api.expect(res, 201, contains={"question_text": text})
    assert body["id"] > 0 and body["created_at"]


@pytest.mark.parametrize("length", [50, 500], ids=["exactly-50", "exactly-500"])
def test_career_question_length_boundaries_accepted(api, length):
    """Career questions of exactly 50 and 500 characters are accepted
    Stories: US-05"""
    student = api.register("student")
    api.expect(api.call("post", "/students/questions", as_=student, json={"question_text": "q" * length}), 201)


@pytest.mark.parametrize("length", [49, 501], ids=["49-chars", "501-chars"])
def test_career_question_length_boundaries_rejected(api, length):
    """Career questions of 49 or 501 characters are rejected
    Stories: US-05"""
    student = api.register("student")
    api.expect(api.call("post", "/students/questions", as_=student, json={"question_text": "q" * length}), 422)


def test_career_question_forbidden_for_mentor(api):
    """A mentor cannot post a career question
    Stories: US-05"""
    mentor = api.register("mentor")
    res = api.call("post", "/students/questions", as_=mentor, json={"question_text": "q" * 60})
    api.expect(res, 403, body={"detail": "Student access required"})


def test_career_question_requires_login(api):
    """A career question cannot be posted without logging in
    Stories: US-05"""
    api.expect(api.call("post", "/students/questions", json={"question_text": "q" * 60}), 401)


# ------------------------------------------------------------------ GET /students/questions


def test_list_career_questions_newest_first(api):
    """A student's questions are listed newest first
    Stories: US-05"""
    student = api.register("student")
    first = api.question(student, "First question " + "a" * 40)
    api.update_row(CareerQuestion, first["id"], created_at=datetime.now(timezone.utc) - timedelta(hours=1))
    api.question(student, "Second question " + "b" * 40)
    body = api.expect(api.call("get", "/students/questions", as_=student), 200)
    assert [q["question_text"][:6] for q in body] == ["Second", "First "]


def test_list_career_questions_only_own(api):
    """A student only sees their own questions
    Stories: US-05"""
    mine, other = api.register("student"), api.register("student", label="student B")
    api.question(other)
    api.expect(api.call("get", "/students/questions", as_=mine), 200, body=[])


def test_list_career_questions_forbidden_for_mentor(api):
    """A mentor cannot list career questions
    Stories: US-05"""
    api.expect(api.call("get", "/students/questions", as_=api.register("mentor")), 403)
