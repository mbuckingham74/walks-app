import os
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

os.environ["MYSQL_HOST"] = "localhost"
os.environ["MYSQL_USER"] = "test"
os.environ["MYSQL_PASSWORD"] = "test"
os.environ["MYSQL_DATABASE"] = "test_walks"
os.environ["API_KEY"] = "test-api-key"
os.environ["SHORTCUT_SECRET"] = "test-shortcut-secret"


@pytest.fixture(scope="session")
def client():
    from app.main import app, get_db

    mock_session = AsyncMock()

    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
