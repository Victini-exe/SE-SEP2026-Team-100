from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    institute_email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="student")


class UserLoginRequest(BaseModel):
    institute_email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserSummary(BaseModel):
    id: int
    name: str
    institute_email: str
    role: str
    account_status: str
