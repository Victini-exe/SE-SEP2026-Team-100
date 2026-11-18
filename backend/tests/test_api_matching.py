"""Matching: GET /matching/recommendations and the scoring service app.services.matching.calculate_match."""

import pytest

from api_testkit import REQUEST_MESSAGE
from app.models import MentorExpertise, MentorProfile, StudentInterest, StudentProfile
from app.services.matching import calculate_match

STUDENT = {
    "career_goal": "Data Science job",
    "current_situation": "Final-year student",
    "preferred_language": "Tamil",
    "career_aspirations": "Become a data scientist",
}


# ------------------------------------------------------------------ GET /matching/recommendations


def test_recommendations_ranked_with_score_and_reasons(api):
    """A student gets mentors ranked by match score, each with the reasons
    Stories: US-10"""
    data = api.interest("Data Science")
    student = api.student(**STUDENT, interest_area_ids=[data])
    strong = api.mentor(name="Strong Match", guidance_types="Data Science careers", preferred_languages="Tamil, English", experience_level="Senior", expertise_area_ids=[data])
    api.mentor(name="Weak Match", guidance_types="Entrepreneurship", preferred_languages="Hindi", experience_level="Recent Graduate")
    body = api.expect(api.call("get", "/matching/recommendations", as_=student), 200)
    recs = body["recommendations"]
    assert [r["mentor_name"] for r in recs] == ["Strong Match", "Weak Match"]
    assert recs[0]["match_score"] > recs[1]["match_score"]
    assert {"Career guidance fit", "Interest overlap matched", "Language match", "Strong experience level"} <= set(recs[0]["match_explanation"])
    assert strong.id  # strong mentor exists


def test_recommendations_limited_to_top_five(api):
    """At most 5 mentors are recommended
    Stories: US-10"""
    student = api.student(**STUDENT)
    for n in range(6):
        api.mentor(name=f"Mentor {n}")
    body = api.expect(api.call("get", "/matching/recommendations", as_=student), 200)
    assert len(body["recommendations"]) == 5


def test_recommendations_skip_paused_full_and_suspended_mentors(api):
    """Paused, full and suspended mentors are not recommended
    Stories: US-08, US-10"""
    student = api.student(**STUDENT)
    api.mentor(name="Paused", pause_status="paused")
    full = api.mentor(name="Full", capacity=1)
    api.relationship(api.register("student", label="student B"), full)
    api.suspend(api.mentor(name="Suspended"))
    api.mentor(name="Available")
    body = api.expect(api.call("get", "/matching/recommendations", as_=student), 200)
    assert [r["mentor_name"] for r in body["recommendations"]] == ["Available"]


def test_recommendations_empty_when_no_mentors(api):
    """With no available mentors the list is empty
    Stories: US-10"""
    student = api.student(**STUDENT)
    api.expect(api.call("get", "/matching/recommendations", as_=student), 200, body={"recommendations": []})


def test_recommendations_need_student_profile(api):
    """A student without a profile cannot get recommendations
    Stories: US-04, US-10"""
    api.expect(api.call("get", "/matching/recommendations", as_=api.register("student")), 404, body={"detail": "Student profile not found"})


def test_recommendations_forbidden_for_mentor(api):
    """A mentor cannot ask for recommendations
    Stories: US-10"""
    api.expect(api.call("get", "/matching/recommendations", as_=api.mentor()), 403, body={"detail": "Student access required"})


def test_recommendations_require_login(api):
    """Recommendations cannot be fetched without logging in
    Stories: US-10"""
    api.expect(api.call("get", "/matching/recommendations"), 401)


@pytest.mark.xfail(strict=True, reason="Recommendations return mentor_id = mentor PROFILE id, but POST /requests expects the mentor USER id, so requesting a recommended mentor fails (404).")
def test_student_can_request_a_recommended_mentor(api):
    """A student sends a request to a mentor straight from the recommendations
    Stories: US-10, US-12"""
    student = api.student(**STUDENT)
    api.register("student", label="student B")  # makes user ids and profile ids differ, as in real data
    api.mentor()
    recommended = api._raw("get", "/matching/recommendations", student).json()["recommendations"][0]
    res = api.call("post", "/requests", as_=student, json={"mentor_id": recommended["mentor_id"], "personal_message": REQUEST_MESSAGE})
    api.expect(res, 201)


# ------------------------------------------------------------------ calculate_match (unit tests)


def _profiles(student_kwargs=None, mentor_kwargs=None, student_interests=(), mentor_expertise=()):
    student = StudentProfile(**(student_kwargs or {}))
    mentor = MentorProfile(**{"pause_status": "active", "max_mentee_capacity": 2, "experience_level": "Recent Graduate", **(mentor_kwargs or {})})
    student.interests = [StudentInterest(interest_area_id=i) for i in student_interests]
    mentor.expertise = [MentorExpertise(interest_area_id=i) for i in mentor_expertise]
    return student, mentor


def test_score_rewards_guidance_fit():
    """Matching goal words in the mentor's guidance types add 35 points
    Stories: US-10"""
    student, mentor = _profiles({"career_goal": "Research career"}, {"guidance_types": "Research"})
    score, reasons = calculate_match(student, mentor)
    assert "Career guidance fit" in reasons and score == 35 + 5 + 5


def test_score_interest_overlap_is_proportional():
    """Interest overlap adds up to 30 points in proportion to shared interests
    Stories: US-10"""
    student, mentor = _profiles(student_interests=[1, 2], mentor_expertise=[2, 3])
    score, reasons = calculate_match(student, mentor)
    assert "Interest overlap matched" in reasons and score == 15 + 5 + 5


def test_score_language_match_and_mismatch():
    """A shared language adds 10 points; a different one is explained
    Stories: US-10"""
    student, mentor = _profiles({"preferred_language": "Hindi"}, {"preferred_languages": "English, Hindi"})
    assert "Language match" in calculate_match(student, mentor)[1]
    student, mentor = _profiles({"preferred_language": "Tamil"}, {"preferred_languages": "English"})
    assert "Language preference does not align" in calculate_match(student, mentor)[1]


@pytest.mark.parametrize("level,points", [("Senior", 10), ("Experienced", 7), ("Recent Graduate", 5)])
def test_score_experience_level(level, points):
    """Senior mentors score higher than experienced, who score higher than recent graduates
    Stories: US-10"""
    student, mentor = _profiles(mentor_kwargs={"experience_level": level})
    assert calculate_match(student, mentor)[0] == points + 5


def test_score_full_mentor_loses_capacity_points():
    """A mentor at capacity loses the availability points
    Stories: US-08, US-10"""
    student, mentor = _profiles(mentor_kwargs={"max_mentee_capacity": 1})
    score, reasons = calculate_match(student, mentor, active_mentee_count=1)
    assert score == 5 and "Capacity or availability unavailable" in reasons


def test_score_never_exceeds_100():
    """The match score is capped at 100
    Stories: US-10"""
    student, mentor = _profiles(
        {"career_goal": "data science analytics", "preferred_language": "English"},
        {"guidance_types": "data science", "organisations": "analytics firm", "preferred_languages": "English", "experience_level": "Senior"},
        student_interests=[1],
        mentor_expertise=[1],
    )
    score, _ = calculate_match(student, mentor)
    assert score == 100
