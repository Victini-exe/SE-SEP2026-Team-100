from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.db.session import get_db
from app.models import MentorApplication, MentorProfile, User
from app.schemas.mentor import MentorApplicationRead, MentorApplicationReview

router = APIRouter()


@router.get("/dashboard")
def admin_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    pending_count = db.query(MentorApplication).filter(MentorApplication.status == "pending").count()
    approved_count = db.query(MentorProfile).join(User, User.id == MentorProfile.user_id).filter(
        MentorProfile.status == "approved",
        User.account_status == "active",
    ).count()
    return {"pending_applications": pending_count, "approved_mentors": approved_count, "recent_activity": []}


@router.get("/users")
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 50,
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    query = db.query(User).order_by(User.created_at.desc())
    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {"id": user.id, "name": user.name, "role": user.role, "account_status": user.account_status}
            for user in users
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get("/applications", response_model=list[MentorApplicationRead])
def list_applications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    applications = db.query(MentorApplication).order_by(MentorApplication.submitted_at.desc()).all()
    return [
        MentorApplicationRead(
            id=a.id,
            user_id=a.user_id,
            roll_number=a.roll_number,
            graduation_year=a.graduation_year,
            linked_in_url=a.linked_in_url,
            additional_verification_info=a.additional_verification_info,
            status=a.status,
            admin_decision=a.admin_decision,
            rejection_reason=a.rejection_reason,
            submitted_at=a.submitted_at.isoformat(),
            decision_at=a.decision_at.isoformat() if a.decision_at else None,
        )
        for a in applications
    ]


@router.post("/applications/{application_id}/review")
def review_application(application_id: int, payload: MentorApplicationReview, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    application = db.query(MentorApplication).filter(MentorApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if payload.action == "reject":
        if not payload.rejection_reason or len(payload.rejection_reason.strip()) < 5:
            raise HTTPException(status_code=400, detail="Rejection reason is required")
        application.status = "rejected"
        application.admin_decision = "rejected"
        application.rejection_reason = payload.rejection_reason
    else:
        application.status = "approved"
        application.admin_decision = "approved"
        application.user.account_status = "active"
        profile = db.query(MentorProfile).filter(MentorProfile.user_id == application.user_id).first()
        if not profile:
            profile = MentorProfile(user_id=application.user_id)
            db.add(profile)
        profile.status = "approved"
    application.decision_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": application.id, "status": application.status, "decision_at": application.decision_at.isoformat()}
