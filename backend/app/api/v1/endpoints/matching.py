from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.api.v1.endpoints.auth import get_current_user
from app.db.session import get_db
from app.models import MentorProfile, MentoringRelationship, StudentProfile, User
from app.services.matching import calculate_match

router = APIRouter()


@router.get("/recommendations")
def recommend_mentors(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access required")
    student_profile = db.query(StudentProfile).options(selectinload(StudentProfile.interests)).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    if not student_profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    active_counts = (
        db.query(
            MentoringRelationship.mentor_id.label("mentor_id"),
            func.count(MentoringRelationship.id).label("active_count"),
        )
        .filter(MentoringRelationship.status == "active")
        .group_by(MentoringRelationship.mentor_id)
        .subquery()
    )
    mentor_profiles = (
        db.query(
            MentorProfile,
            User,
            func.coalesce(active_counts.c.active_count, 0).label("active_count"),
        )
        .join(User, User.id == MentorProfile.user_id)
        .outerjoin(active_counts, active_counts.c.mentor_id == MentorProfile.user_id)
        .options(selectinload(MentorProfile.expertise))
        .filter(
            MentorProfile.status == "approved",
            MentorProfile.pause_status == "active",
            User.account_status == "active",
            func.coalesce(active_counts.c.active_count, 0) < MentorProfile.max_mentee_capacity,
        )
        .all()
    )
    recommendations = []
    for mentor, mentor_user, active_count in mentor_profiles:
        score, reasons = calculate_match(student_profile, mentor, active_count)
        recommendations.append({
            "mentor_id": mentor.id,
            "mentor_name": mentor_user.name,
            "match_score": score,
            "match_explanation": reasons,
        })

    recommendations.sort(key=lambda item: item["match_score"], reverse=True)
    return {"recommendations": recommendations[:5]}
