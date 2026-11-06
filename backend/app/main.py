from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.config import get_settings
from app.db.session import initialize_database

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description=(
        "IITM BS mentoring platform API. Protected endpoints require a bearer token. "
        "Request expiry is evaluated when request lists, decisions, or new requests are processed. "
        "Suspension blocks protected actions and pauses active relationships; reactivation resumes "
        "a relationship only when the other participant is not suspended."
    ),
    openapi_tags=[
        {"name": "auth", "description": "Registration, login, and authenticated identity."},
        {"name": "students", "description": "Student profile and career-question operations."},
        {"name": "mentors", "description": "Mentor applications, profiles, discovery, and search."},
        {"name": "admin", "description": "Mentor application review and user listing."},
        {"name": "matching", "description": "Explainable mentor recommendations."},
        {"name": "mentoring lifecycle", "description": "Requests, relationships, sessions, messages, notes, reports, analytics, and notifications."},
    ],
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health_check():
    return {"status": "ok"}
