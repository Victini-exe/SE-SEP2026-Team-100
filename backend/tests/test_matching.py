from app.models import MentorProfile, StudentProfile
from app.services.matching import calculate_match


def test_matching_score_ranks_overlap():
    student = StudentProfile(career_goal="Data Science", preferred_language="English", current_situation="Graduating soon")
    mentor = MentorProfile(career_history="AI", guidance_types="Data Science, Career mentoring", preferred_languages="English", experience_level="Senior", pause_status="active", max_mentee_capacity=3)
    student.interests = []
    mentor.expertise = []
    score, reasons = calculate_match(student, mentor)
    assert score > 0
    assert "Career guidance fit" in reasons or "Good experience level" in reasons
