from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.db.session import get_db
from app.models import InterestArea, MentorApplication, MentorExpertise, MentorProfile, MentoringRelationship, User
from app.schemas.mentor import MentorApplicationCreate, MentorApplicationRead, MentorApplicationReview, MentorProfileCreate, MentorProfileRead, MentorSearchRequest

router = APIRouter()


@router.post("/apply", response_model=MentorApplicationRead, status_code=201)
def apply_as_mentor(payload: MentorApplicationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "mentor":
        raise HTTPException(status_code=403, detail="Mentor role required")
    existing = db.query(MentorApplication).filter(MentorApplication.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Application already submitted")
    application = MentorApplication(
        user_id=current_user.id,
        roll_number=payload.roll_number,
        graduation_year=payload.graduation_year,
        linked_in_url=payload.linked_in_url,
        additional_verification_info=payload.additional_verification_info,
        status="pending",
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return MentorApplicationRead(
        id=application.id,
        user_id=application.user_id,
        roll_number=application.roll_number,
        graduation_year=application.graduation_year,
        linked_in_url=application.linked_in_url,
        additional_verification_info=application.additional_verification_info,
        status=application.status,
        admin_decision=application.admin_decision,
        rejection_reason=application.rejection_reason,
        submitted_at=application.submitted_at.isoformat(),
        decision_at=application.decision_at.isoformat() if application.decision_at else None,
    )


@router.get("/me/profile", response_model=MentorProfileRead)
def get_mentor_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "mentor":
        raise HTTPException(status_code=403, detail="Mentor access required")
    profile = db.query(MentorProfile).filter(MentorProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Mentor profile not found")
    current_count = db.query(MentoringRelationship).filter(
        MentoringRelationship.mentor_id == current_user.id,
        MentoringRelationship.status == "active",
    ).count()
    return MentorProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        career_history=profile.career_history,
        organisations=profile.organisations,
        roles=profile.roles,
        years_of_experience=profile.years_of_experience,
        graduation_year=profile.graduation_year,
        experience_level=profile.experience_level,
        guidance_types=profile.guidance_types,
        preferred_languages=profile.preferred_languages,
        max_mentee_capacity=profile.max_mentee_capacity,
        availability=profile.availability,
        pause_status=profile.pause_status,
        status=profile.status,
        expertise_area_ids=[item.interest_area_id for item in profile.expertise],
        current_mentee_count=current_count,
    )


@router.put("/me/profile", response_model=MentorProfileRead)
def update_mentor_profile(payload: MentorProfileCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "mentor":
        raise HTTPException(status_code=403, detail="Mentor access required")
    profile = db.query(MentorProfile).filter(MentorProfile.user_id == current_user.id).first()
    if not profile:
        profile = MentorProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    profile.career_history = payload.career_history
    profile.organisations = payload.organisations
    profile.roles = payload.roles
    profile.years_of_experience = payload.years_of_experience
    profile.graduation_year = payload.graduation_year
    profile.experience_level = payload.experience_level
    profile.guidance_types = payload.guidance_types
    profile.preferred_languages = payload.preferred_languages
    profile.max_mentee_capacity = payload.max_mentee_capacity
    profile.availability = payload.availability
    profile.pause_status = payload.pause_status

    db.query(MentorExpertise).filter(MentorExpertise.mentor_profile_id == profile.id).delete()
    for interest_id in payload.expertise_area_ids[:10]:
        if db.query(InterestArea).filter(InterestArea.id == interest_id).first():
            db.add(MentorExpertise(mentor_profile_id=profile.id, interest_area_id=interest_id))

    db.commit()
    db.refresh(profile)
    current_count = db.query(MentoringRelationship).filter(
        MentoringRelationship.mentor_id == current_user.id,
        MentoringRelationship.status == "active",
    ).count()
    return MentorProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        career_history=profile.career_history,
        organisations=profile.organisations,
        roles=profile.roles,
        years_of_experience=profile.years_of_experience,
        graduation_year=profile.graduation_year,
        experience_level=profile.experience_level,
        guidance_types=profile.guidance_types,
        preferred_languages=profile.preferred_languages,
        max_mentee_capacity=profile.max_mentee_capacity,
        availability=profile.availability,
        pause_status=profile.pause_status,
        status=profile.status,
        expertise_area_ids=[item.interest_area_id for item in profile.expertise],
        current_mentee_count=current_count,
    )


@router.get("/search")
def search_mentors(
    query: str | None = None,
    domain: str | None = None,
    guidance_type: str | None = None,
    industry: str | None = None,
    graduation_year: int | None = None,
    language: str | None = None,
    experience_level: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    active_counts = (
        db.query(
            MentoringRelationship.mentor_id.label("mentor_id"),
            func.count(MentoringRelationship.id).label("active_count"),
        )
        .filter(MentoringRelationship.status == "active")
        .group_by(MentoringRelationship.mentor_id)
        .subquery()
    )
    base = (
        db.query(MentorProfile, User, func.coalesce(active_counts.c.active_count, 0).label("active_count"))
        .join(User, User.id == MentorProfile.user_id)
        .outerjoin(active_counts, active_counts.c.mentor_id == MentorProfile.user_id)
        .filter(
            MentorProfile.status == "approved",
            MentorProfile.pause_status == "active",
            User.account_status == "active",
            func.coalesce(active_counts.c.active_count, 0) < MentorProfile.max_mentee_capacity,
        )
    )
    if query:
        pattern = f"%{query}%"
        base = base.filter(User.name.ilike(pattern) | MentorProfile.roles.ilike(pattern))
    if domain:
        base = base.filter(MentorProfile.organisations.ilike(f"%{domain}%"))
    if guidance_type:
        base = base.filter(MentorProfile.guidance_types.ilike(f"%{guidance_type}%"))
    if industry:
        base = base.filter(MentorProfile.organisations.ilike(f"%{industry}%"))
    if graduation_year:
        base = base.filter(MentorProfile.graduation_year == graduation_year)
    if language:
        base = base.filter(MentorProfile.preferred_languages.ilike(f"%{language}%"))
    if experience_level:
        base = base.filter(MentorProfile.experience_level == experience_level)
    total = base.count()
    rows = base.order_by(User.name).offset((page - 1) * page_size).limit(page_size).all()
    items = [
        {
            "id": mentor.id,
            "user_id": mentor.user_id,
            "name": user.name,
            "experience_level": mentor.experience_level,
            "roles": mentor.roles,
            "organisations": mentor.organisations,
            "preferred_languages": mentor.preferred_languages,
            "guidance_types": mentor.guidance_types,
            "status": mentor.status,
            "max_mentee_capacity": mentor.max_mentee_capacity,
            "current_mentee_count": active_count,
        }
        for mentor, user, active_count in rows
    ]
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@router.get("/{mentor_id}")
def get_public_mentor_profile(mentor_id: int, db: Session = Depends(get_db)):
    mentor = db.query(MentorProfile).filter(MentorProfile.id == mentor_id, MentorProfile.status == "approved").first()
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")
    user = db.query(User).filter(User.id == mentor.user_id).first()
    return {
        "id": mentor.id,
        "name": user.name if user else "",
        "career_history": mentor.career_history,
        "organisations": mentor.organisations,
        "roles": mentor.roles,
        "years_of_experience": mentor.years_of_experience,
        "experience_level": mentor.experience_level,
        "guidance_types": mentor.guidance_types,
        "preferred_languages": mentor.preferred_languages,
        "availability": mentor.availability,
        "max_mentee_capacity": mentor.max_mentee_capacity,
        "match_score": 0,
        "match_explanation": [],
    }
