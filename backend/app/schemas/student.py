from typing import Optional

from pydantic import BaseModel, Field


class StudentProfileCreate(BaseModel):
    career_goal: Optional[str] = Field(default=None, max_length=1000)
    current_situation: Optional[str] = Field(default=None, max_length=1000)
    preferred_language: Optional[str] = Field(default=None, max_length=100)
    weekly_availability: Optional[str] = Field(default=None, max_length=1000)
    career_aspirations: Optional[str] = Field(default=None, max_length=2000)
    interest_area_ids: list[int] = Field(default_factory=list)


class StudentProfileRead(StudentProfileCreate):
    id: int
    user_id: int


class CareerQuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=50, max_length=500)


class CareerQuestionRead(CareerQuestionCreate):
    id: int
    created_at: str
