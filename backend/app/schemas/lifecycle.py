from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class MentoringRequestCreate(BaseModel):
    mentor_id: int = Field(gt=0)
    personal_message: str = Field(min_length=100, max_length=1000)
    career_question_id: int | None = Field(default=None, gt=0)

    @field_validator("personal_message")
    @classmethod
    def require_message_content(cls, value: str) -> str:
        if len(value.strip()) < 100:
            raise ValueError("Personal message must contain at least 100 non-whitespace characters")
        return value


class MentoringDecision(BaseModel):
    action: Literal["accept", "decline"]
    decline_reason: str | None = Field(default=None, max_length=1000)


class RelationshipClose(BaseModel):
    reason: Literal["GOAL_ACHIEVED", "NO_LONGER_NEEDED", "NOT_A_GOOD_FIT", "OTHER"]
    explanation: str | None = Field(default=None, max_length=1000)


class SessionProposal(BaseModel):
    scheduled_for: datetime
    timezone: str = Field(min_length=1, max_length=100)
    meeting_link: str | None = Field(default=None, max_length=500)


class SessionDecision(BaseModel):
    action: Literal["confirm", "unavailable", "cancel", "complete"]


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def require_message_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message cannot be blank")
        return value


class SessionNoteCreate(BaseModel):
    notes: str = Field(min_length=1, max_length=10000)
    action_items: str | None = Field(default=None, max_length=5000)
    due_at: datetime | None = None


class ReportCreate(BaseModel):
    target_user_id: int = Field(gt=0)
    category: Literal["HARASSMENT", "INAPPROPRIATE_BEHAVIOUR", "SPAM", "MISREPRESENTATION", "OTHER"]
    description: str = Field(min_length=20, max_length=4000)

    @field_validator("description")
    @classmethod
    def require_description_content(cls, value: str) -> str:
        if len(value.strip()) < 20:
            raise ValueError("Description must contain at least 20 non-whitespace characters")
        return value


class ReportReview(BaseModel):
    status: Literal["under_review", "resolved", "dismissed"]
    admin_review_notes: str = Field(min_length=5, max_length=4000)


class AccountStatusChange(BaseModel):
    reason: str = Field(min_length=10, max_length=2000)

    @field_validator("reason")
    @classmethod
    def require_reason_content(cls, value: str) -> str:
        if len(value.strip()) < 10:
            raise ValueError("Reason must contain at least 10 non-whitespace characters")
        return value
