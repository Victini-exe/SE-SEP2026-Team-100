from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    institute_email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    account_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("role IN ('student', 'mentor', 'admin')", name="ck_users_role"),
        CheckConstraint("account_status IN ('active', 'suspended', 'pending_verification')", name="ck_users_account_status"),
    )

    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    mentor_profile = relationship("MentorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    mentor_applications = relationship("MentorApplication", back_populates="user", cascade="all, delete-orphan")
    career_questions = relationship("CareerQuestion", back_populates="user", cascade="all, delete-orphan")
    student_mentoring_requests = relationship(
        "MentoringRequest",
        foreign_keys="[MentoringRequest.student_id]",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    mentor_mentoring_requests = relationship(
        "MentoringRequest",
        foreign_keys="[MentoringRequest.mentor_id]",
        back_populates="mentor",
        cascade="all, delete-orphan",
    )
    student_mentoring_relationships = relationship(
        "MentoringRelationship",
        foreign_keys="[MentoringRelationship.student_id]",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    mentor_mentoring_relationships = relationship(
        "MentoringRelationship",
        foreign_keys="[MentoringRelationship.mentor_id]",
        back_populates="mentor",
        cascade="all, delete-orphan",
    )
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    career_goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_situation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    weekly_availability: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    career_aspirations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    profile_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="student_profile")
    interests = relationship("StudentInterest", back_populates="student_profile", cascade="all, delete-orphan")


class MentorProfile(Base):
    __tablename__ = "mentor_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    career_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organisations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    roles: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    years_of_experience: Mapped[int] = mapped_column(Integer, default=0)
    graduation_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    experience_level: Mapped[str] = mapped_column(String(30), default="Recent Graduate")
    guidance_types: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_languages: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    max_mentee_capacity: Mapped[int] = mapped_column(Integer, default=1)
    availability: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pause_status: Mapped[str] = mapped_column(String(20), default="active")
    status: Mapped[str] = mapped_column(String(20), default="unapproved")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="mentor_profile")
    expertise = relationship("MentorExpertise", back_populates="mentor_profile", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("experience_level IN ('Recent Graduate', 'Experienced', 'Senior')", name="ck_mentor_experience_level"),
        CheckConstraint("pause_status IN ('active', 'paused')", name="ck_mentor_pause_status"),
        CheckConstraint("status IN ('approved', 'unapproved', 'rejected', 'suspended')", name="ck_mentor_status"),
        CheckConstraint("max_mentee_capacity BETWEEN 1 AND 5", name="ck_mentor_capacity_range"),
    )


class MentorApplication(Base):
    __tablename__ = "mentor_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    roll_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    graduation_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    linked_in_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    additional_verification_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    admin_decision: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    decision_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="mentor_applications")

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_mentor_application_user"),
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_mentor_application_status"),
    )


class InterestArea(Base):
    __tablename__ = "interest_areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    student_interests = relationship("StudentInterest", back_populates="interest_area", cascade="all, delete-orphan")
    mentor_expertise = relationship("MentorExpertise", back_populates="interest_area", cascade="all, delete-orphan")


class StudentInterest(Base):
    __tablename__ = "student_interests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    interest_area_id: Mapped[int] = mapped_column(ForeignKey("interest_areas.id", ondelete="CASCADE"), nullable=False)

    student_profile = relationship("StudentProfile", back_populates="interests")
    interest_area = relationship("InterestArea", back_populates="student_interests")

    __table_args__ = (UniqueConstraint("student_profile_id", "interest_area_id", name="uq_student_interest"),)


class MentorExpertise(Base):
    __tablename__ = "mentor_expertise"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    mentor_profile_id: Mapped[int] = mapped_column(ForeignKey("mentor_profiles.id", ondelete="CASCADE"), nullable=False)
    interest_area_id: Mapped[int] = mapped_column(ForeignKey("interest_areas.id", ondelete="CASCADE"), nullable=False)

    mentor_profile = relationship("MentorProfile", back_populates="expertise")
    interest_area = relationship("InterestArea", back_populates="mentor_expertise")

    __table_args__ = (UniqueConstraint("mentor_profile_id", "interest_area_id", name="uq_mentor_expertise"),)


class CareerQuestion(Base):
    __tablename__ = "career_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="career_questions")


class MentoringRequest(Base):
    __tablename__ = "mentoring_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mentor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    personal_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    decision_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    student = relationship("User", foreign_keys="[MentoringRequest.student_id]", back_populates="student_mentoring_requests")
    mentor = relationship("User", foreign_keys="[MentoringRequest.mentor_id]", back_populates="mentor_mentoring_requests")

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'accepted', 'rejected', 'expired')", name="ck_mentoring_request_status"),
        UniqueConstraint("student_id", "mentor_id", "status", name="uq_student_mentor_request_active"),
    )


class MentoringRelationship(Base):
    __tablename__ = "mentoring_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mentor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    student = relationship("User", foreign_keys="[MentoringRelationship.student_id]", back_populates="student_mentoring_relationships")
    mentor = relationship("User", foreign_keys="[MentoringRelationship.mentor_id]", back_populates="mentor_mentoring_relationships")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    mentoring_relationship_id: Mapped[int] = mapped_column(ForeignKey("mentoring_relationships.id", ondelete="CASCADE"), nullable=False)
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    meeting_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SessionNote(Base):
    __tablename__ = "session_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    action: Mapped[str] = mapped_column(String(150), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="audit_logs")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="notifications")
