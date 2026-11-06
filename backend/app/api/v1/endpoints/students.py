from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.db.session import get_db
from app.models import CareerQuestion, InterestArea, StudentInterest, StudentProfile, User
from app.schemas.student import CareerQuestionCreate, CareerQuestionRead, StudentProfileCreate, StudentProfileRead

router = APIRouter()


@router.get("/me/profile", response_model=StudentProfileRead)
def get_student_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access required")
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return StudentProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        career_goal=profile.career_goal,
        current_situation=profile.current_situation,
        preferred_language=profile.preferred_language,
        weekly_availability=profile.weekly_availability,
        career_aspirations=profile.career_aspirations,
        interest_area_ids=[item.interest_area_id for item in profile.interests],
    )


@router.put("/me/profile", response_model=StudentProfileRead)
def update_student_profile(payload: StudentProfileCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access required")

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    profile.career_goal = payload.career_goal
    profile.current_situation = payload.current_situation
    profile.preferred_language = payload.preferred_language
    profile.weekly_availability = payload.weekly_availability
    profile.career_aspirations = payload.career_aspirations

    db.query(StudentInterest).filter(StudentInterest.student_profile_id == profile.id).delete()
    for interest_id in payload.interest_area_ids[:5]:
        interest = db.query(InterestArea).filter(InterestArea.id == interest_id).first()
        if interest:
            db.add(StudentInterest(student_profile_id=profile.id, interest_area_id=interest.id))

    db.commit()
    db.refresh(profile)
    return StudentProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        career_goal=profile.career_goal,
        current_situation=profile.current_situation,
        preferred_language=profile.preferred_language,
        weekly_availability=profile.weekly_availability,
        career_aspirations=profile.career_aspirations,
        interest_area_ids=[item.interest_area_id for item in profile.interests],
    )


@router.get("/questions", response_model=list[CareerQuestionRead])
def list_career_questions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access required")
    questions = db.query(CareerQuestion).filter(CareerQuestion.user_id == current_user.id).order_by(CareerQuestion.created_at.desc()).all()
    return [CareerQuestionRead(id=q.id, question_text=q.question_text, created_at=q.created_at.isoformat()) for q in questions]


@router.post("/questions", response_model=CareerQuestionRead, status_code=status.HTTP_201_CREATED)
def create_career_question(payload: CareerQuestionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access required")
    item = CareerQuestion(user_id=current_user.id, question_text=payload.question_text)
    db.add(item)
    db.commit()
    db.refresh(item)
    return CareerQuestionRead(id=item.id, question_text=item.question_text, created_at=item.created_at.isoformat())
