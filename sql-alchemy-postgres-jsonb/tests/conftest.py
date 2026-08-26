import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app import app
from db import engine


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        with engine.begin() as connection:
            connection.execute(text("TRUNCATE TABLE documents RESTART IDENTITY"))
        yield test_client
