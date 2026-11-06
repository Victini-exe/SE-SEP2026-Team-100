from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.db.session import get_db
from app.models import MentorProfile, StudentProfile, User
from app.services.matching import calculate_match

router = APIRouter()


@router.get("/recommendations")
def recommend_mentors(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access required")
    student_profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not student_profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    mentor_profiles = db.query(MentorProfile).filter(MentorProfile.status == "approved", MentorProfile.pause_status == "active").all()
    recommendations = []
    for mentor in mentor_profiles:
        mentor_user = db.query(User).filter(User.id == mentor.user_id).first()
        if not mentor_user or mentor_user.account_status == "suspended":
            continue
        score, reasons = calculate_match(student_profile, mentor)
        recommendations.append({
            "mentor_id": mentor.id,
            "mentor_name": mentor_user.name,
            "match_score": score,
            "match_explanation": reasons,
        })

    recommendations.sort(key=lambda item: item["match_score"], reverse=True)
    return {"recommendations": recommendations[:5]}
