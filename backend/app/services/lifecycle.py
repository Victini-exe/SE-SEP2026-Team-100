from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import MentoringRequest, Notification


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def notify(db: Session, user_id: int, kind: str, message: str, entity_id: int | None = None) -> None:
    db.add(Notification(user_id=user_id, notification_type=kind, message=message, entity_id=entity_id))


def expire_requests(db: Session, mentor_id: int | None = None) -> int:
    cutoff = utc_now() - timedelta(days=7)
    query = db.query(MentoringRequest).filter(
        MentoringRequest.status == "pending",
        MentoringRequest.created_at < cutoff,
    )
    if mentor_id is not None:
        query = query.filter(MentoringRequest.mentor_id == mentor_id)
    expired = query.all()
    now = utc_now()
    for request in expired:
        request.status = "expired"
        request.decision_at = now
        notify(db, request.student_id, "request_expired", "Your mentoring request expired.", request.id)
        notify(db, request.mentor_id, "request_expired", "A mentoring request expired.", request.id)
    return len(expired)
