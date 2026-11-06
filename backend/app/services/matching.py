from app.models import MentorProfile, StudentProfile


def calculate_match(student_profile: StudentProfile, mentor_profile: MentorProfile):
    reasons = []
    score = 0.0

    if student_profile.career_goal and mentor_profile.guidance_types:
        if student_profile.career_goal.lower() in mentor_profile.guidance_types.lower():
            score += 30
            reasons.append("Career guidance fit")
        else:
            reasons.append("Career goal guidance not strongly aligned")

    student_interests = {item.interest_area_id for item in student_profile.interests}
    mentor_expertise = {item.interest_area_id for item in mentor_profile.expertise}
    overlap = len(student_interests & mentor_expertise)
    if overlap:
        score += 30
        reasons.append("Interest overlap matched")
    else:
        reasons.append("No direct expertise overlap")

    if mentor_profile.organisations and student_profile.current_situation:
        score += 15
        reasons.append("Industry context available")
    else:
        reasons.append("No explicit industry fit evidence")

    if student_profile.preferred_language and mentor_profile.preferred_languages:
        if student_profile.preferred_language.lower() in mentor_profile.preferred_languages.lower():
            score += 10
            reasons.append("Language match")
        else:
            reasons.append("Language preference does not align")

    if mentor_profile.experience_level == "Senior":
        score += 10
        reasons.append("Strong experience level")
    elif mentor_profile.experience_level == "Experienced":
        score += 8
        reasons.append("Good experience level")

    if mentor_profile.pause_status == "active" and mentor_profile.max_mentee_capacity > 0:
        score += 5
        reasons.append("Availability and capacity open")
    else:
        reasons.append("Capacity or availability unavailable")

    return round(min(score, 100), 2), reasons
