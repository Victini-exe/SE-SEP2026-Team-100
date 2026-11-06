from typing import Optional

from pydantic import BaseModel, Field


class MentorProfileCreate(BaseModel):
    career_history: Optional[str] = Field(default=None, max_length=4000)
    organisations: Optional[str] = Field(default=None, max_length=2000)
    roles: Optional[str] = Field(default=None, max_length=2000)
    years_of_experience: int = Field(default=0, ge=0)
    graduation_year: Optional[int] = Field(default=None, ge=1950, le=2100)
    experience_level: str = Field(default="Recent Graduate")
    guidance_types: Optional[str] = Field(default=None, max_length=2000)
    preferred_languages: Optional[str] = Field(default=None, max_length=500)
    max_mentee_capacity: int = Field(default=1, ge=1, le=5)
    availability: Optional[str] = Field(default=None, max_length=1000)
    pause_status: str = Field(default="active")
    expertise_area_ids: list[int] = Field(default_factory=list)


class MentorProfileRead(MentorProfileCreate):
    id: int
    user_id: int
    status: str
    current_mentee_count: int = 0


class MentorApplicationCreate(BaseModel):
    roll_number: Optional[str] = Field(default=None, max_length=50)
    graduation_year: Optional[int] = Field(default=None, ge=1950, le=2100)
    linked_in_url: Optional[str] = Field(default=None, max_length=500)
    additional_verification_info: Optional[str] = Field(default=None, max_length=4000)


class MentorApplicationReview(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    rejection_reason: Optional[str] = Field(default=None, max_length=1000)


class MentorApplicationRead(MentorApplicationCreate):
    id: int
    user_id: int
    status: str
    admin_decision: Optional[str] = None
    rejection_reason: Optional[str] = None
    submitted_at: str
    decision_at: Optional[str] = None


class MentorSearchRequest(BaseModel):
    query: Optional[str] = None
    domain: Optional[str] = None
    guidance_type: Optional[str] = None
    industry: Optional[str] = None
    graduation_year: Optional[int] = None
    language: Optional[str] = None
    sort_by: str = "match_score"
    page: int = 1
    page_size: int = 10
