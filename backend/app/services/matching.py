from app.models import MentorProfile, StudentProfile


def calculate_match(
    student_profile: StudentProfile,
    mentor_profile: MentorProfile,
    active_mentee_count: int = 0,
):
    reasons = []
    score = 0.0

    goals = " ".join(filter(None, (student_profile.career_goal, student_profile.career_aspirations))).lower()
    guidance = (mentor_profile.guidance_types or "").lower()
    if goals and guidance:
        if any(term in guidance for term in goals.split() if len(term) > 3):
            score += 35
            reasons.append("Career guidance fit")
        else:
            reasons.append("Career goal guidance not strongly aligned")

    student_interests = {item.interest_area_id for item in student_profile.interests}
    mentor_expertise = {item.interest_area_id for item in mentor_profile.expertise}
    overlap = len(student_interests & mentor_expertise)
    if overlap:
        score += min(30, 30 * overlap / max(len(student_interests), 1))
        reasons.append("Interest overlap matched")
    elif student_interests and mentor_expertise:
        reasons.append("No direct expertise overlap")

    organisations = (mentor_profile.organisations or "").lower()
    if organisations and goals and any(term in organisations for term in goals.split() if len(term) > 3):
        score += 15
        reasons.append("Industry context aligns with career goal")

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
        score += 7
        reasons.append("Good experience level")
    elif mentor_profile.experience_level == "Recent Graduate":
        score += 5
        reasons.append("Recent graduate perspective")

    if (
        mentor_profile.pause_status == "active"
        and active_mentee_count < mentor_profile.max_mentee_capacity
    ):
        score += 5
        reasons.append("Availability and capacity open")
    else:
        reasons.append("Capacity or availability unavailable")

    return round(min(score, 100), 2), reasons
