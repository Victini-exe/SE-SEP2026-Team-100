from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.models import User
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest, UserSummary

router = APIRouter()
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.institute_email == email.lower()).first()


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if user.account_status == "suspended":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")
    return user


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    if user.account_status == "suspended":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")
    return user


@router.post("/register", response_model=UserSummary, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    if not payload.institute_email:
        raise HTTPException(status_code=400, detail="Email is required")

    email = str(payload.institute_email).lower()
    email_domain = email.rpartition("@")[2]
    if email_domain not in settings.allowed_domains:
        raise HTTPException(status_code=400, detail="Institute email domain not allowed")

    if get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="User already exists")

    role = payload.role.lower()
    if role not in {"student", "mentor"}:
        raise HTTPException(status_code=400, detail="Only student and mentor registration is available")

    user = User(
        name=payload.name,
        institute_email=email,
        password_hash=get_password_hash(payload.password),
        role=role,
        account_status="active" if role != "mentor" else "pending_verification",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserSummary(id=user.id, name=user.name, institute_email=user.institute_email, role=user.role, account_status=user.account_status)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.institute_email.lower(), payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    token = create_access_token(user.institute_email)
    return TokenResponse(access_token=token)


@router.post("/login-form", response_model=TokenResponse)
def login_form(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return TokenResponse(access_token=create_access_token(user.institute_email))


@router.get("/me", response_model=UserSummary)
def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserSummary:
    return UserSummary(id=current_user.id, name=current_user.name, institute_email=current_user.institute_email, role=current_user.role, account_status=current_user.account_status)


@router.post("/logout")
def logout():
    return {"detail": "Logged out"}
