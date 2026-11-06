"""Extend the foundation schema for mentoring lifecycle and moderation.

Revision ID: b7a1_lifecycle
Revises: a54322c1d4af
"""

from alembic import op
import sqlalchemy as sa

revision = "b7a1_lifecycle"
down_revision = "a54322c1d4af"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("suspended_from_status", sa.String(length=20), nullable=True))
    with op.batch_alter_table("mentoring_requests") as batch:
        batch.drop_constraint("uq_student_mentor_request_active", type_="unique")
        batch.drop_constraint("ck_mentoring_request_status", type_="check")
        batch.add_column(sa.Column("career_question_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("decline_reason", sa.Text(), nullable=True))
        batch.add_column(sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_foreign_key(
            "fk_mentoring_requests_career_question",
            "career_questions",
            ["career_question_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_check_constraint(
            "ck_mentoring_request_status",
            "status IN ('pending', 'accepted', 'rejected', 'withdrawn', 'expired')",
        )
    op.create_index(
        "uq_pending_student_mentor_request",
        "mentoring_requests",
        ["student_id", "mentor_id"],
        unique=True,
        sqlite_where=sa.text("status = 'pending'"),
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.create_index("ix_request_student_status_created", "mentoring_requests", ["student_id", "status", "created_at"])
    op.create_index("ix_request_mentor_status_created", "mentoring_requests", ["mentor_id", "status", "created_at"])
    with op.batch_alter_table("mentoring_relationships") as batch:
        batch.add_column(sa.Column("closure_reason", sa.String(length=30), nullable=True))
        batch.add_column(sa.Column("closure_details", sa.Text(), nullable=True))
        batch.add_column(sa.Column("closed_by_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_foreign_key("fk_relationship_closed_by", "users", ["closed_by_id"], ["id"])
        batch.create_check_constraint("ck_relationship_status", "status IN ('active', 'closed', 'suspended')")
        batch.create_check_constraint(
            "ck_relationship_closure_reason",
            "closure_reason IS NULL OR closure_reason IN ('GOAL_ACHIEVED', 'NO_LONGER_NEEDED', 'NOT_A_GOOD_FIT', 'OTHER')",
        )
    op.execute("UPDATE mentoring_relationships SET last_activity_at = started_at WHERE last_activity_at IS NULL")
    op.create_index("ix_relationship_student_status", "mentoring_relationships", ["student_id", "status"])
    op.create_index("ix_relationship_mentor_status", "mentoring_relationships", ["mentor_id", "status"])
    op.create_index("ix_relationship_activity", "mentoring_relationships", ["status", "last_activity_at"])
    op.execute("UPDATE sessions SET status = 'confirmed' WHERE status = 'scheduled'")
    with op.batch_alter_table("sessions") as batch:
        batch.add_column(sa.Column("proposer_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("proposer_timezone", sa.String(length=100), nullable=True))
        batch.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_foreign_key("fk_sessions_proposer", "users", ["proposer_id"], ["id"], ondelete="CASCADE")
        batch.create_check_constraint(
            "ck_session_status",
            "status IN ('proposed', 'confirmed', 'unavailable', 'completed', 'cancelled')",
        )
    op.execute("UPDATE sessions SET proposer_timezone = 'UTC' WHERE proposer_timezone IS NULL")
    op.execute("UPDATE sessions SET updated_at = created_at WHERE updated_at IS NULL")
    op.create_index("ix_sessions_relationship_time", "sessions", ["mentoring_relationship_id", "scheduled_for"])
    with op.batch_alter_table("messages") as batch:
        batch.alter_column("session_id", existing_type=sa.Integer(), nullable=True)
        batch.add_column(sa.Column("mentoring_relationship_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("recipient_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.create_foreign_key("fk_messages_relationship", "mentoring_relationships", ["mentoring_relationship_id"], ["id"], ondelete="CASCADE")
        batch.create_foreign_key("fk_messages_recipient", "users", ["recipient_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_messages_relationship_created", "messages", ["mentoring_relationship_id", "created_at"])
    with op.batch_alter_table("session_notes") as batch:
        batch.add_column(sa.Column("action_items", sa.Text(), nullable=True))
        batch.add_column(sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("submitted_late", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE session_notes SET updated_at = created_at WHERE updated_at IS NULL")
    with op.batch_alter_table("reports") as batch:
        batch.add_column(sa.Column("category", sa.String(length=40), nullable=False, server_default="other"))
        batch.add_column(sa.Column("admin_review_notes", sa.Text(), nullable=True))
        batch.add_column(sa.Column("reviewed_by_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("decision_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_foreign_key("fk_reports_reviewed_by", "users", ["reviewed_by_id"], ["id"])
        batch.create_check_constraint(
            "ck_report_status",
            "status IN ('open', 'under_review', 'resolved', 'dismissed')",
        )
    op.create_index("ix_reports_status_created", "reports", ["status", "created_at"])
    with op.batch_alter_table("notifications") as batch:
        batch.add_column(sa.Column("notification_type", sa.String(length=50), nullable=False, server_default="general"))
        batch.add_column(sa.Column("entity_id", sa.Integer(), nullable=True))
    op.create_index("ix_notifications_user_read_created", "notifications", ["user_id", "is_read", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_read_created", table_name="notifications")
    with op.batch_alter_table("notifications") as batch:
        batch.drop_column("entity_id")
        batch.drop_column("notification_type")
    with op.batch_alter_table("reports") as batch:
        batch.drop_constraint("ck_report_status", type_="check")
        batch.drop_constraint("fk_reports_reviewed_by", type_="foreignkey")
        batch.drop_column("decision_at")
        batch.drop_column("reviewed_by_id")
        batch.drop_column("admin_review_notes")
        batch.drop_column("category")
    op.drop_index("ix_reports_status_created", table_name="reports")
    op.drop_index("ix_messages_relationship_created", table_name="messages")
    with op.batch_alter_table("session_notes") as batch:
        batch.drop_column("updated_at")
        batch.drop_column("submitted_late")
        batch.drop_column("due_at")
        batch.drop_column("action_items")
    with op.batch_alter_table("messages") as batch:
        batch.drop_constraint("fk_messages_recipient", type_="foreignkey")
        batch.drop_constraint("fk_messages_relationship", type_="foreignkey")
        batch.drop_column("is_read")
        batch.drop_column("recipient_id")
        batch.drop_column("mentoring_relationship_id")
        batch.alter_column("session_id", existing_type=sa.Integer(), nullable=False)
    with op.batch_alter_table("sessions") as batch:
        batch.drop_constraint("ck_session_status", type_="check")
        batch.drop_constraint("fk_sessions_proposer", type_="foreignkey")
        batch.drop_column("updated_at")
        batch.drop_column("proposer_timezone")
        batch.drop_column("proposer_id")
    op.drop_index("ix_sessions_relationship_time", table_name="sessions")
    op.drop_index("ix_relationship_activity", table_name="mentoring_relationships")
    op.drop_index("ix_relationship_mentor_status", table_name="mentoring_relationships")
    op.drop_index("ix_relationship_student_status", table_name="mentoring_relationships")
    with op.batch_alter_table("mentoring_relationships") as batch:
        batch.drop_constraint("ck_relationship_closure_reason", type_="check")
        batch.drop_constraint("ck_relationship_status", type_="check")
        batch.drop_constraint("fk_relationship_closed_by", type_="foreignkey")
        batch.drop_column("last_activity_at")
        batch.drop_column("closed_by_id")
        batch.drop_column("closure_details")
        batch.drop_column("closure_reason")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("suspended_from_status")
    op.drop_index("ix_request_mentor_status_created", table_name="mentoring_requests")
    op.drop_index("ix_request_student_status_created", table_name="mentoring_requests")
    op.drop_index("uq_pending_student_mentor_request", table_name="mentoring_requests")
    with op.batch_alter_table("mentoring_requests") as batch:
        batch.drop_constraint("ck_mentoring_request_status", type_="check")
        batch.drop_constraint("fk_mentoring_requests_career_question", type_="foreignkey")
        batch.drop_column("withdrawn_at")
        batch.drop_column("decline_reason")
        batch.drop_column("career_question_id")
        batch.create_unique_constraint("uq_student_mentor_request_active", ["student_id", "mentor_id", "status"])
        batch.create_check_constraint(
            "ck_mentoring_request_status",
            "status IN ('pending', 'accepted', 'rejected', 'expired')",
        )
