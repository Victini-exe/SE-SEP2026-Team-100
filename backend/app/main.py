from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.config import get_settings
from app.db.session import engine, initialize_database

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.on_event("startup")
def create_db_tables() -> None:
    initialize_database()


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
