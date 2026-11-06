from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession, joinedload, selectinload

from app.api.v1.endpoints.auth import get_current_user
from app.db.session import get_db
from app.models import (
    AuditLog,
    CareerQuestion,
    InterestArea,
    MentorProfile,
    MentoringRelationship,
    MentoringRequest,
    Message,
    MentorExpertise,
    Notification,
    Report,
    Session as MentoringSession,
    SessionNote,
    StudentInterest,
    StudentProfile,
    User,
)
from app.schemas.lifecycle import (
    AccountStatusChange,
    MentoringDecision,
    MentoringRequestCreate,
    MessageCreate,
    RelationshipClose,
    ReportCreate,
    ReportReview,
    SessionDecision,
    SessionNoteCreate,
    SessionProposal,
)
from app.services.lifecycle import aware_utc, expire_requests, notify, utc_now

router = APIRouter()


def _require_role(user: User, role: str) -> None:
    if user.role != role:
        raise HTTPException(status_code=403, detail=f"{role.title()} access required")


def _relationship(db: DbSession, relationship_id: int, user_id: int) -> MentoringRelationship:
    relationship = db.query(MentoringRelationship).filter(
        MentoringRelationship.id == relationship_id,
        (MentoringRelationship.student_id == user_id) | (MentoringRelationship.mentor_id == user_id),
    ).first()
    if relationship is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return relationship


def _active_relationship(db: DbSession, relationship_id: int, user_id: int) -> MentoringRelationship:
    relationship = _relationship(db, relationship_id, user_id)
    if relationship.status != "active":
        raise HTTPException(status_code=409, detail="Relationship is not active")
    return relationship


def _session_for_participant(db: DbSession, session_id: int, user_id: int) -> tuple[MentoringSession, MentoringRelationship]:
    item = db.query(MentoringSession).filter(MentoringSession.id == session_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Session not found")
    relationship = _relationship(db, item.mentoring_relationship_id, user_id)
    return item, relationship


def _session_time_utc(value: datetime, timezone_name: str) -> datetime:
    try:
        tz = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(status_code=422, detail="Unknown timezone") from exc
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc)
    first = value.replace(tzinfo=tz, fold=0)
    second = value.replace(tzinfo=tz, fold=1)
    if (
        first.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) != value
        and second.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) != value
    ):
        raise HTTPException(status_code=422, detail="Local time does not exist in this timezone")
    if first.utcoffset() != second.utcoffset():
        raise HTTPException(status_code=422, detail="Ambiguous local time; include an explicit UTC offset")
    return first.astimezone(timezone.utc)


def _request_view(item: MentoringRequest, include_student: bool = False) -> dict:
    result = {
        "id": item.id,
        "student_id": item.student_id,
        "mentor_id": item.mentor_id,
        "personal_message": item.personal_message,
        "career_question_id": item.career_question_id,
        "decline_reason": item.decline_reason,
        "status": item.status,
        "created_at": aware_utc(item.created_at).isoformat(),
        "decision_at": aware_utc(item.decision_at).isoformat() if item.decision_at else None,
        "withdrawn_at": aware_utc(item.withdrawn_at).isoformat() if item.withdrawn_at else None,
    }
    if include_student:
        result["student"] = {
            "name": item.student.name,
            "career_goal": item.student.student_profile.career_goal if item.student.student_profile else None,
            "current_situation": item.student.student_profile.current_situation if item.student.student_profile else None,
            "career_question": item.career_question.question_text if item.career_question else None,
        }
    return result


@router.post("/requests", status_code=status.HTTP_201_CREATED)
def create_request(
    payload: MentoringRequestCreate,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    _require_role(current_user, "student")
    db.query(User).filter(User.id == current_user.id).with_for_update().first()
    expire_requests(db)
    mentor = db.query(User).filter(User.id == payload.mentor_id, User.role == "mentor").first()
    profile = db.query(MentorProfile).filter(MentorProfile.user_id == payload.mentor_id).first()
    if mentor is None or profile is None or profile.status != "approved" or mentor.account_status != "active":
        raise HTTPException(status_code=404, detail="Available mentor not found")
    if profile.pause_status != "active":
        raise HTTPException(status_code=409, detail="Mentor is not accepting requests")
    active_count = db.query(MentoringRelationship).filter(
        MentoringRelationship.mentor_id == mentor.id,
        MentoringRelationship.status == "active",
    ).count()
    if active_count >= profile.max_mentee_capacity:
        raise HTTPException(status_code=409, detail="Mentor is at capacity")
    pending_count = db.query(MentoringRequest).filter(
        MentoringRequest.student_id == current_user.id,
        MentoringRequest.status == "pending",
    ).count()
    if pending_count >= 3:
        raise HTTPException(status_code=409, detail="At most three mentoring requests may be pending")
    duplicate = db.query(MentoringRequest).filter(
        MentoringRequest.student_id == current_user.id,
        MentoringRequest.mentor_id == mentor.id,
        MentoringRequest.status == "pending",
    ).first()
    active_pair = db.query(MentoringRelationship).filter(
        MentoringRelationship.student_id == current_user.id,
        MentoringRelationship.mentor_id == mentor.id,
        MentoringRelationship.status == "active",
    ).first()
    if duplicate or active_pair:
        raise HTTPException(status_code=409, detail="A pending request or active relationship already exists")
    if payload.career_question_id is not None:
        question = db.query(CareerQuestion).filter(
            CareerQuestion.id == payload.career_question_id,
            CareerQuestion.user_id == current_user.id,
        ).first()
        if question is None:
            raise HTTPException(status_code=404, detail="Career question not found")
    item = MentoringRequest(
        student_id=current_user.id,
        mentor_id=mentor.id,
        personal_message=payload.personal_message,
        career_question_id=payload.career_question_id,
    )
    db.add(item)
    try:
        db.flush()
        notify(db, mentor.id, "new_request", "You received a mentoring request.", item.id)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A pending request already exists for this mentor") from exc
    db.refresh(item)
    return _request_view(item)


@router.get("/requests")
def list_requests(
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    expire_requests(db, current_user.id if current_user.role == "mentor" else None)
    if current_user.role == "student":
        query = db.query(MentoringRequest).filter(MentoringRequest.student_id == current_user.id)
        include_student = False
    elif current_user.role == "mentor":
        query = db.query(MentoringRequest).options(
            joinedload(MentoringRequest.student).joinedload(User.student_profile),
            joinedload(MentoringRequest.career_question),
        ).filter(MentoringRequest.mentor_id == current_user.id)
        include_student = True
    else:
        raise HTTPException(status_code=403, detail="Student or mentor access required")
    db.commit()
    items = query.order_by(MentoringRequest.created_at.desc()).limit(100).all()
    return {"items": [_request_view(item, include_student) for item in items]}


@router.post("/requests/{request_id}/decision")
def decide_request(
    request_id: int,
    payload: MentoringDecision,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    _require_role(current_user, "mentor")
    expire_requests(db, current_user.id)
    item = db.query(MentoringRequest).filter(
        MentoringRequest.id == request_id,
        MentoringRequest.mentor_id == current_user.id,
    ).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Request not found")
    if item.status != "pending":
        raise HTTPException(status_code=409, detail=f"Request is {item.status}")
    if payload.action == "accept":
        profile = db.query(MentorProfile).filter(
            MentorProfile.user_id == current_user.id,
        ).with_for_update().first()
        if profile is None or profile.status != "approved" or profile.pause_status != "active":
            raise HTTPException(status_code=409, detail="Mentor is unavailable")
        mentor_user = db.query(User).filter(User.id == current_user.id).with_for_update().first()
        if mentor_user is None or mentor_user.account_status != "active":
            raise HTTPException(status_code=403, detail="Mentor account is unavailable")
        active_count = db.query(MentoringRelationship).filter(
            MentoringRelationship.mentor_id == current_user.id,
            MentoringRelationship.status == "active",
        ).count()
        if active_count >= profile.max_mentee_capacity:
            raise HTTPException(status_code=409, detail="Mentor is at capacity")
        existing = db.query(MentoringRelationship).filter(
            MentoringRelationship.student_id == item.student_id,
            MentoringRelationship.mentor_id == item.mentor_id,
            MentoringRelationship.status == "active",
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="An active relationship already exists")
        item.status = "accepted"
        relationship = MentoringRelationship(student_id=item.student_id, mentor_id=item.mentor_id)
        db.add(relationship)
        db.flush()
        notify(db, item.student_id, "request_accepted", "Your mentoring request was accepted.", relationship.id)
    else:
        item.status = "rejected"
        item.decline_reason = payload.decline_reason
        notify(db, item.student_id, "request_declined", "Your mentoring request was declined.", item.id)
    item.decision_at = utc_now()
    db.commit()
    return {"id": item.id, "status": item.status, "decision_at": aware_utc(item.decision_at).isoformat()}


@router.post("/requests/{request_id}/withdraw")
def withdraw_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    _require_role(current_user, "student")
    item = db.query(MentoringRequest).filter(
        MentoringRequest.id == request_id,
        MentoringRequest.student_id == current_user.id,
    ).with_for_update().first()
    if item is None:
        raise HTTPException(status_code=404, detail="Request not found")
    if item.status != "pending":
        raise HTTPException(status_code=409, detail="Only pending requests can be withdrawn")
    item.status = "withdrawn"
    item.withdrawn_at = utc_now()
    notify(db, item.mentor_id, "request_withdrawn", "A mentoring request was withdrawn.", item.id)
    db.commit()
    return {"id": item.id, "status": item.status, "withdrawn_at": aware_utc(item.withdrawn_at).isoformat()}


@router.get("/relationships")
def list_relationships(
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    query = db.query(MentoringRelationship).options(
        joinedload(MentoringRelationship.student).joinedload(User.student_profile).selectinload(StudentProfile.interests).joinedload(
            StudentInterest.interest_area
        ),
        joinedload(MentoringRelationship.student).selectinload(User.career_questions),
        joinedload(MentoringRelationship.mentor).joinedload(User.mentor_profile).selectinload(MentorProfile.expertise).joinedload(
            MentorExpertise.interest_area
        ),
        joinedload(MentoringRelationship.mentor),
    ).filter(
        (MentoringRelationship.student_id == current_user.id)
        | (MentoringRelationship.mentor_id == current_user.id)
    )
    return {
        "items": [
            {
                "id": row.id,
                "student_id": row.student_id,
                "mentor_id": row.mentor_id,
                "student_name": row.student.name,
                "mentor_name": row.mentor.name,
                "status": row.status,
                "started_at": aware_utc(row.started_at).isoformat(),
                "ended_at": aware_utc(row.ended_at).isoformat() if row.ended_at else None,
                "closure_reason": row.closure_reason,
                "last_activity_at": aware_utc(row.last_activity_at).isoformat(),
                "student_career_goal": row.student.student_profile.career_goal if row.student.student_profile else None,
                "student_interests": [
                    interest.interest_area.name
                    for interest in row.student.student_profile.interests
                    if interest.interest_area
                ] if row.student.student_profile else [],
                "current_question": max(
                    row.student.career_questions,
                    key=lambda question: question.created_at,
                    default=None,
                ).question_text if row.student.career_questions else None,
                "mentor_career_history": row.mentor.mentor_profile.career_history if row.mentor.mentor_profile else None,
                "mentor_expertise": [
                    expertise.interest_area.name
                    for expertise in row.mentor.mentor_profile.expertise
                    if expertise.interest_area
                ] if row.mentor.mentor_profile else [],
            }
            for row in query.order_by(MentoringRelationship.started_at.desc()).limit(100).all()
        ]
    }


@router.post("/relationships/{relationship_id}/close")
def close_relationship(
    relationship_id: int,
    payload: RelationshipClose,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    relationship = _active_relationship(db, relationship_id, current_user.id)
    if payload.reason == "OTHER" and not (payload.explanation and payload.explanation.strip()):
        raise HTTPException(status_code=422, detail="An explanation is required for OTHER")
    now = utc_now()
    relationship.status = "closed"
    relationship.ended_at = now
    relationship.closure_reason = payload.reason
    relationship.closure_details = payload.explanation
    relationship.closed_by_id = current_user.id
    relationship.last_activity_at = now
    other_id = relationship.mentor_id if current_user.id == relationship.student_id else relationship.student_id
    notify(db, other_id, "relationship_closed", "A mentoring relationship was closed.", relationship.id)
    db.commit()
    return {"id": relationship.id, "status": relationship.status, "ended_at": now.isoformat()}


@router.post("/relationships/{relationship_id}/sessions", status_code=status.HTTP_201_CREATED)
def propose_session(
    relationship_id: int,
    payload: SessionProposal,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    relationship = _active_relationship(db, relationship_id, current_user.id)
    session = MentoringSession(
        mentoring_relationship_id=relationship.id,
        proposer_id=current_user.id,
        proposer_timezone=payload.timezone,
        scheduled_for=_session_time_utc(payload.scheduled_for, payload.timezone),
        meeting_link=payload.meeting_link,
        status="proposed",
    )
    relationship.last_activity_at = utc_now()
    db.add(session)
    other_id = relationship.mentor_id if current_user.id == relationship.student_id else relationship.student_id
    db.flush()
    notify(db, other_id, "session_proposed", "A mentoring session was proposed.", session.id)
    db.commit()
    db.refresh(session)
    return {
        "id": session.id,
        "scheduled_for": aware_utc(session.scheduled_for).isoformat(),
        "proposer_timezone": session.proposer_timezone,
        "status": session.status,
        "meeting_link": session.meeting_link,
    }


@router.get("/relationships/{relationship_id}/sessions")
def list_sessions(
    relationship_id: int,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    _relationship(db, relationship_id, current_user.id)
    rows = db.query(MentoringSession).filter(
        MentoringSession.mentoring_relationship_id == relationship_id
    ).order_by(MentoringSession.scheduled_for.desc()).limit(100).all()
    return {
        "items": [
            {
                "id": row.id,
                "scheduled_for": aware_utc(row.scheduled_for).isoformat() if row.scheduled_for else None,
                "proposer_id": row.proposer_id,
                "proposer_timezone": row.proposer_timezone,
                "status": row.status,
                "meeting_link": row.meeting_link,
            }
            for row in rows
        ]
    }


@router.post("/sessions/{session_id}/decision")
def decide_session(
    session_id: int,
    payload: SessionDecision,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    session, relationship = _session_for_participant(db, session_id, current_user.id)
    if relationship.status != "active":
        raise HTTPException(status_code=409, detail="Relationship is not active")
    if payload.action == "complete":
        if session.status != "confirmed" or session.scheduled_for is None or aware_utc(session.scheduled_for) > utc_now():
            raise HTTPException(status_code=409, detail="Only past confirmed sessions can be completed")
        session.status = "completed"
    elif payload.action == "cancel":
        if current_user.id != session.proposer_id or session.status not in {"proposed", "confirmed"}:
            raise HTTPException(status_code=409, detail="Only the proposer may cancel this session")
        session.status = "cancelled"
    else:
        if current_user.id == session.proposer_id or session.status != "proposed":
            raise HTTPException(status_code=409, detail="Only the other participant may decide a proposal")
        session.status = "confirmed" if payload.action == "confirm" else "unavailable"
    session.updated_at = utc_now()
    relationship.last_activity_at = utc_now()
    db.commit()
    return {"id": session.id, "status": session.status, "scheduled_for": aware_utc(session.scheduled_for).isoformat()}


@router.get("/relationships/{relationship_id}/messages")
def list_messages(
    relationship_id: int,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    relationship = _relationship(db, relationship_id, current_user.id)
    rows = db.query(Message).filter(
        Message.mentoring_relationship_id == relationship.id
    ).order_by(Message.created_at.desc()).limit(100).all()
    for row in rows:
        if row.recipient_id == current_user.id:
            row.is_read = True
    db.commit()
    return {
        "items": [
            {
                "id": row.id,
                "sender_id": row.sender_id,
                "recipient_id": row.recipient_id,
                "content": row.content,
                "is_read": row.is_read,
                "created_at": aware_utc(row.created_at).isoformat(),
            }
            for row in reversed(rows)
        ]
    }


@router.post("/relationships/{relationship_id}/messages", status_code=status.HTTP_201_CREATED)
def send_message(
    relationship_id: int,
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    relationship = _active_relationship(db, relationship_id, current_user.id)
    recipient_id = relationship.mentor_id if current_user.id == relationship.student_id else relationship.student_id
    recipient = db.query(User).filter(User.id == recipient_id, User.account_status == "active").first()
    if recipient is None:
        raise HTTPException(status_code=409, detail="Recipient account is unavailable")
    row = Message(
        mentoring_relationship_id=relationship.id,
        sender_id=current_user.id,
        recipient_id=recipient_id,
        content=payload.content,
    )
    relationship.last_activity_at = utc_now()
    db.add(row)
    db.flush()
    notify(db, recipient_id, "new_message", "You have a new mentoring message.", relationship.id)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "created_at": aware_utc(row.created_at).isoformat()}


@router.post("/sessions/{session_id}/notes", status_code=status.HTTP_201_CREATED)
def add_session_note(
    session_id: int,
    payload: SessionNoteCreate,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    session, relationship = _session_for_participant(db, session_id, current_user.id)
    if session.scheduled_for is None:
        raise HTTPException(status_code=409, detail="Session has no scheduled time")
    session_time = aware_utc(session.scheduled_for)
    if utc_now() < session_time:
        raise HTTPException(status_code=409, detail="Notes can be added after the session")
    late = utc_now() > session_time + timedelta(hours=48)
    note = SessionNote(
        session_id=session.id,
        author_id=current_user.id,
        notes=payload.notes,
        action_items=payload.action_items,
        due_at=payload.due_at,
        submitted_late=late,
    )
    relationship.last_activity_at = utc_now()
    db.add(note)
    db.commit()
    db.refresh(note)
    return {
        "id": note.id,
        "notes": note.notes,
        "action_items": note.action_items,
        "due_at": aware_utc(note.due_at).isoformat() if note.due_at else None,
        "submitted_late": note.submitted_late,
        "created_at": aware_utc(note.created_at).isoformat(),
    }


@router.get("/sessions/{session_id}/notes")
def list_session_notes(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    _session_for_participant(db, session_id, current_user.id)
    rows = db.query(SessionNote).filter(SessionNote.session_id == session_id).order_by(SessionNote.created_at.asc()).all()
    return {
        "items": [
            {
                "id": row.id,
                "author_id": row.author_id,
                "notes": row.notes,
                "action_items": row.action_items,
                "due_at": aware_utc(row.due_at).isoformat() if row.due_at else None,
                "submitted_late": row.submitted_late,
                "created_at": aware_utc(row.created_at).isoformat(),
            }
            for row in rows
        ]
    }


@router.post("/reports", status_code=status.HTTP_201_CREATED)
def create_report(
    payload: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    if current_user.role not in {"student", "mentor"}:
        raise HTTPException(status_code=403, detail="Only students and mentors may submit reports")
    if payload.target_user_id == current_user.id:
        raise HTTPException(status_code=422, detail="You cannot report yourself")
    target = db.query(User).filter(User.id == payload.target_user_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="Reported user not found")
    duplicate = db.query(Report).filter(
        Report.reporter_id == current_user.id,
        Report.target_user_id == target.id,
        Report.status.in_(["open", "under_review"]),
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="An unresolved report for this user already exists")
    report = Report(
        reporter_id=current_user.id,
        target_user_id=target.id,
        category=payload.category.lower(),
        reason=payload.description,
    )
    db.add(report)
    db.flush()
    admin_ids = [row.id for row in db.query(User.id).filter(User.role == "admin", User.account_status == "active").all()]
    for admin_id in admin_ids:
        notify(db, admin_id, "new_report", "A user report requires review.", report.id)
    db.commit()
    db.refresh(report)
    return {"id": report.id, "status": report.status, "created_at": aware_utc(report.created_at).isoformat()}


@router.get("/admin/reports")
def list_reports(
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    _require_role(current_user, "admin")
    rows = db.query(Report).order_by(Report.created_at.desc()).limit(200).all()
    return {
        "items": [
            {
                "id": row.id,
                "reporter_id": row.reporter_id,
                "target_user_id": row.target_user_id,
                "category": row.category,
                "description": row.reason,
                "status": row.status,
                "admin_review_notes": row.admin_review_notes,
                "created_at": aware_utc(row.created_at).isoformat(),
            }
            for row in rows
        ]
    }


@router.post("/admin/reports/{report_id}/review")
def review_report(
    report_id: int,
    payload: ReportReview,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    _require_role(current_user, "admin")
    report = db.query(Report).filter(Report.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status in {"resolved", "dismissed"}:
        raise HTTPException(status_code=409, detail="Report has already been resolved")
    report.status = payload.status
    report.admin_review_notes = payload.admin_review_notes
    report.reviewed_by_id = current_user.id
    report.decision_at = utc_now() if payload.status in {"resolved", "dismissed"} else None
    db.add(AuditLog(
        user_id=current_user.id,
        action="report_reviewed",
        entity_type="report",
        entity_id=report.id,
        details=f"status={payload.status}",
    ))
    db.commit()
    return {"id": report.id, "status": report.status}


@router.post("/admin/users/{user_id}/suspend")
def suspend_user(
    user_id: int,
    payload: AccountStatusChange,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    _require_role(current_user, "admin")
    target = db.query(User).filter(User.id == user_id).with_for_update().first()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == current_user.id:
        raise HTTPException(status_code=409, detail="Administrators cannot suspend their own account")
    if target.account_status == "suspended":
        raise HTTPException(status_code=409, detail="User is already suspended")
    target.suspended_from_status = target.account_status
    target.account_status = "suspended"
    relationships = db.query(MentoringRelationship).filter(
        MentoringRelationship.status == "active",
        (MentoringRelationship.student_id == user_id) | (MentoringRelationship.mentor_id == user_id),
    ).all()
    for relationship in relationships:
        relationship.status = "suspended"
        relationship.last_activity_at = utc_now()
    db.add(AuditLog(user_id=current_user.id, action="account_suspended", entity_type="user", entity_id=user_id, details=payload.reason))
    db.commit()
    return {"id": user_id, "account_status": target.account_status, "suspended_relationships": len(relationships)}


@router.post("/admin/users/{user_id}/reactivate")
def reactivate_user(
    user_id: int,
    payload: AccountStatusChange,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    _require_role(current_user, "admin")
    target = db.query(User).filter(User.id == user_id).with_for_update().first()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.account_status != "suspended":
        raise HTTPException(status_code=409, detail="User is not suspended")
    target.account_status = target.suspended_from_status or "active"
    target.suspended_from_status = None
    suspended = db.query(MentoringRelationship).filter(
        MentoringRelationship.status == "suspended",
        (MentoringRelationship.student_id == user_id) | (MentoringRelationship.mentor_id == user_id),
    ).all()
    for relationship in suspended:
        other_id = relationship.mentor_id if relationship.student_id == user_id else relationship.student_id
        other = db.query(User).filter(User.id == other_id).first()
        if other is not None and other.account_status != "suspended":
            relationship.status = "active"
            relationship.last_activity_at = utc_now()
    db.add(AuditLog(user_id=current_user.id, action="account_reactivated", entity_type="user", entity_id=user_id, details=payload.reason))
    db.commit()
    return {"id": user_id, "account_status": target.account_status}


@router.get("/admin/alerts")
def admin_alerts(
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    _require_role(current_user, "admin")
    now = utc_now()
    stale_requests = db.query(MentoringRequest).filter(
        MentoringRequest.status == "pending",
        MentoringRequest.created_at < now - timedelta(days=5),
    ).order_by(MentoringRequest.created_at.asc()).limit(100).all()
    inactive_relationships = db.query(MentoringRelationship).filter(
        MentoringRelationship.status == "active",
        MentoringRelationship.last_activity_at < now - timedelta(days=30),
    ).order_by(MentoringRelationship.last_activity_at.asc()).limit(100).all()
    return {
        "stale_requests": [{"id": row.id, "mentor_id": row.mentor_id, "created_at": aware_utc(row.created_at).isoformat()} for row in stale_requests],
        "inactive_relationships": [{"id": row.id, "status": row.status, "last_activity_at": aware_utc(row.last_activity_at).isoformat()} for row in inactive_relationships],
    }


@router.get("/admin/analytics")
def admin_analytics(
    start: datetime | None = None,
    end: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    _require_role(current_user, "admin")
    lower = aware_utc(start) if start else datetime.min.replace(tzinfo=timezone.utc)
    upper = aware_utc(end) if end else utc_now()
    if lower > upper:
        raise HTTPException(status_code=422, detail="Start must not be after end")
    request_count = db.query(MentoringRequest).filter(MentoringRequest.created_at >= lower, MentoringRequest.created_at <= upper).count()
    accepted_count = db.query(MentoringRequest).filter(
        MentoringRequest.created_at >= lower,
        MentoringRequest.created_at <= upper,
        MentoringRequest.status == "accepted",
    ).count()
    session_count = db.query(MentoringSession).filter(MentoringSession.created_at >= lower, MentoringSession.created_at <= upper).count()
    active_mentors = db.query(User).join(MentorProfile, MentorProfile.user_id == User.id).filter(
        User.account_status == "active",
        MentorProfile.status == "approved",
    ).count()
    active_mentees = db.query(User).join(MentoringRelationship, MentoringRelationship.student_id == User.id).filter(
        User.account_status == "active",
        MentoringRelationship.status == "active",
    ).distinct().count()
    active_relationships = db.query(MentoringRelationship).filter(MentoringRelationship.status == "active").count()
    goal_counts = db.query(
        StudentProfile.career_goal,
        func.count(StudentProfile.id).label("total"),
    ).filter(
        StudentProfile.career_goal.isnot(None),
    ).group_by(StudentProfile.career_goal).order_by(func.count(StudentProfile.id).desc()).limit(10).all()
    interest_counts = db.query(
        InterestArea.name,
        func.count(StudentInterest.id).label("total"),
    ).join(StudentInterest, StudentInterest.interest_area_id == InterestArea.id).group_by(
        InterestArea.name
    ).order_by(func.count(StudentInterest.id).desc()).limit(10).all()
    active_by_mentor = db.query(
        MentoringRelationship.mentor_id.label("mentor_id"),
        func.count(MentoringRelationship.id).label("active_count"),
    ).filter(MentoringRelationship.status == "active").group_by(
        MentoringRelationship.mentor_id
    ).subquery()
    mentor_rows = db.query(
        MentorProfile.organisations,
        MentorProfile.max_mentee_capacity,
        func.coalesce(active_by_mentor.c.active_count, 0),
    ).join(User, User.id == MentorProfile.user_id).outerjoin(
        active_by_mentor, active_by_mentor.c.mentor_id == MentorProfile.user_id
    ).filter(
        User.account_status == "active",
        MentorProfile.status == "approved",
        MentorProfile.pause_status == "active",
    ).all()
    domain_supply: dict[str, int] = {}
    for organizations, capacity, active_count in mentor_rows:
        if organizations:
            domain = organizations.strip()
            domain_supply[domain] = domain_supply.get(domain, 0) + max(0, capacity - active_count)
    sparse_domains = [
        {"domain": domain, "available_capacity": capacity}
        for domain, capacity in sorted(domain_supply.items(), key=lambda item: item[1])
        if capacity < 3
    ][:10]
    relationship_dates = db.query(MentoringRelationship.started_at).filter(
        MentoringRelationship.started_at >= lower,
        MentoringRelationship.started_at <= upper,
    ).all()
    monthly_participation: dict[str, int] = {}
    for (started_at,) in relationship_dates:
        month = aware_utc(started_at).strftime("%Y-%m")
        monthly_participation[month] = monthly_participation.get(month, 0) + 1
    return {
        "active_mentors": active_mentors,
        "active_mentees": active_mentees,
        "active_relationships": active_relationships,
        "requests": request_count,
        "accepted_requests": accepted_count,
        "acceptance_rate": round(accepted_count / request_count, 4) if request_count else 0,
        "sessions": session_count,
        "career_goals": [
            {"goal": goal, "count": count} for goal, count in goal_counts if count >= 3
        ],
        "popular_interest_areas": [
            {"interest": name, "count": count} for name, count in interest_counts if count >= 3
        ],
        "insufficient_mentor_availability": sparse_domains,
        "participation_trends": [
            {"month": month, "relationships_started": count}
            for month, count in sorted(monthly_participation.items())
        ],
        "period": {"start": lower.isoformat(), "end": upper.isoformat()},
    }


@router.get("/notifications")
def list_notifications(
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    rows = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(100).all()
    return {
        "items": [
            {"id": row.id, "type": row.notification_type, "message": row.message, "entity_id": row.entity_id, "is_read": row.is_read, "created_at": aware_utc(row.created_at).isoformat()}
            for row in rows
        ]
    }


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    row = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    row.is_read = True
    db.commit()
    return {"id": row.id, "is_read": row.is_read}
