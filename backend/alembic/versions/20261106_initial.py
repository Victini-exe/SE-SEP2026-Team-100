"""initial schema

Revision ID: a54322c1d4af
Revises: 
Create Date: 2026-11-06 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a54322c1d4af"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("institute_email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("account_status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institute_email", name="uq_users_institute_email"),
        sa.CheckConstraint("role IN ('student', 'mentor', 'admin')", name="ck_users_role"),
        sa.CheckConstraint("account_status IN ('active', 'suspended', 'pending_verification')", name="ck_users_account_status"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_institute_email"), "users", ["institute_email"], unique=False)

    op.create_table(
        "student_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("career_goal", sa.Text(), nullable=True),
        sa.Column("current_situation", sa.Text(), nullable=True),
        sa.Column("preferred_language", sa.String(length=50), nullable=True),
        sa.Column("weekly_availability", sa.Text(), nullable=True),
        sa.Column("career_aspirations", sa.Text(), nullable=True),
        sa.Column("profile_history", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_student_profiles_user_id"),
    )
    op.create_index(op.f("ix_student_profiles_id"), "student_profiles", ["id"], unique=False)

    op.create_table(
        "mentor_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("career_history", sa.Text(), nullable=True),
        sa.Column("organisations", sa.Text(), nullable=True),
        sa.Column("roles", sa.Text(), nullable=True),
        sa.Column("years_of_experience", sa.Integer(), nullable=False),
        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.Column("experience_level", sa.String(length=30), nullable=False),
        sa.Column("guidance_types", sa.Text(), nullable=True),
        sa.Column("preferred_languages", sa.Text(), nullable=True),
        sa.Column("max_mentee_capacity", sa.Integer(), nullable=False),
        sa.Column("availability", sa.Text(), nullable=True),
        sa.Column("pause_status", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_mentor_profiles_user_id"),
        sa.CheckConstraint("experience_level IN ('Recent Graduate', 'Experienced', 'Senior')", name="ck_mentor_experience_level"),
        sa.CheckConstraint("pause_status IN ('active', 'paused')", name="ck_mentor_pause_status"),
        sa.CheckConstraint("status IN ('approved', 'unapproved', 'rejected', 'suspended')", name="ck_mentor_status"),
        sa.CheckConstraint("max_mentee_capacity BETWEEN 1 AND 5", name="ck_mentor_capacity_range"),
    )
    op.create_index(op.f("ix_mentor_profiles_id"), "mentor_profiles", ["id"], unique=False)

    op.create_table(
        "mentor_applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("roll_number", sa.String(length=50), nullable=True),
        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.Column("linked_in_url", sa.String(length=500), nullable=True),
        sa.Column("additional_verification_info", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("admin_decision", sa.String(length=30), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decision_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_mentor_application_user"),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_mentor_application_status"),
    )
    op.create_index(op.f("ix_mentor_applications_id"), "mentor_applications", ["id"], unique=False)

    op.create_table(
        "interest_areas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_interest_areas_name"),
    )
    op.create_index(op.f("ix_interest_areas_id"), "interest_areas", ["id"], unique=False)

    op.create_table(
        "student_interests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_profile_id", sa.Integer(), nullable=False),
        sa.Column("interest_area_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["interest_area_id"], ["interest_areas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_profile_id"], ["student_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_profile_id", "interest_area_id", name="uq_student_interest"),
    )
    op.create_index(op.f("ix_student_interests_id"), "student_interests", ["id"], unique=False)

    op.create_table(
        "mentor_expertise",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mentor_profile_id", sa.Integer(), nullable=False),
        sa.Column("interest_area_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["interest_area_id"], ["interest_areas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["mentor_profile_id"], ["mentor_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mentor_profile_id", "interest_area_id", name="uq_mentor_expertise"),
    )
    op.create_index(op.f("ix_mentor_expertise_id"), "mentor_expertise", ["id"], unique=False)

    op.create_table(
        "career_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_career_questions_id"), "career_questions", ["id"], unique=False)

    op.create_table(
        "mentoring_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("mentor_id", sa.Integer(), nullable=False),
        sa.Column("personal_message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decision_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["mentor_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "mentor_id", "status", name="uq_student_mentor_request_active"),
        sa.CheckConstraint("status IN ('pending', 'accepted', 'rejected', 'expired')", name="ck_mentoring_request_status"),
    )
    op.create_index(op.f("ix_mentoring_requests_id"), "mentoring_requests", ["id"], unique=False)

    op.create_table(
        "mentoring_relationships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("mentor_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["mentor_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mentoring_relationships_id"), "mentoring_relationships", ["id"], unique=False)

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mentoring_relationship_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("meeting_link", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["mentoring_relationship_id"], ["mentoring_relationships.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sessions_id"), "sessions", ["id"], unique=False)

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_messages_id"), "messages", ["id"], unique=False)

    op.create_table(
        "session_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_session_notes_id"), "session_notes", ["id"], unique=False)

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reporter_id", sa.Integer(), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_id"), "reports", ["id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=150), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_id"), "notifications", ["id"], unique=False)


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("audit_logs")
    op.drop_table("reports")
    op.drop_table("session_notes")
    op.drop_table("messages")
    op.drop_table("sessions")
    op.drop_table("mentoring_relationships")
    op.drop_table("mentoring_requests")
    op.drop_table("career_questions")
    op.drop_table("mentor_expertise")
    op.drop_table("student_interests")
    op.drop_table("interest_areas")
    op.drop_table("mentor_applications")
    op.drop_table("mentor_profiles")
    op.drop_table("student_profiles")
    op.drop_table("users")
