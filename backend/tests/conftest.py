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
from app.api.v1.endpoints import auth as auth_endpoints  # noqa: E402

# bcrypt's default cost makes every register/login take ~0.3 s. Tests only
# need a correct hash, not a slow one, so use the minimum cost (4 rounds).
auth_endpoints.pwd_context.update(bcrypt__rounds=4)

# Shared API test helpers: actors, the test-case recorder and data builders,
# plus the --case-report option used to build the Milestone 3 test-case document.
from api_testkit import *  # noqa: E402,F401,F403


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_database() -> Iterator[None]:
    yield
    from app.db.session import engine

    engine.dispose()
    TEST_DATABASE_DIRECTORY.cleanup()


@pytest.fixture(autouse=True)
def clean_database() -> Iterator[None]:
    """Start every test from empty tables so counts and ids are predictable."""
    from app.db.base import Base
    from app.db.session import engine, initialize_database

    initialize_database()
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
    yield


@pytest.fixture
def client() -> Iterator[TestClient]:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
