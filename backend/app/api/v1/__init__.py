from fastapi import APIRouter

from app.api.v1.endpoints import auth, admin, students, mentors, matching

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(mentors.router, prefix="/mentors", tags=["mentors"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(matching.router, prefix="/matching", tags=["matching"])
