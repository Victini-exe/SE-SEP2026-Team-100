from collections.abc import Iterator
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "backend" / "app.db"

if DB_PATH.exists():
    DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH.as_posix()}"

# Ensure the app settings resolve against this exact DB before the app imports.
from app.config import get_settings  # noqa: F401


@pytest.fixture
def client() -> Iterator[TestClient]:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
