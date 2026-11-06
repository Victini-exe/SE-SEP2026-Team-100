from collections.abc import Iterator
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from fastapi.testclient import TestClient

TEST_DATABASE_DIRECTORY = TemporaryDirectory(prefix="team100-test-")
DB_PATH = Path(TEST_DATABASE_DIRECTORY.name) / "test.db"

os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH.as_posix()}"

# Ensure the app settings resolve against this exact DB before the app imports.
from app.config import get_settings  # noqa: F401


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_database() -> Iterator[None]:
    yield
    from app.db.session import engine

    engine.dispose()
    TEST_DATABASE_DIRECTORY.cleanup()


@pytest.fixture
def client() -> Iterator[TestClient]:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
