import aiosqlite
import pytest
from fastapi.testclient import TestClient

from dao import GameDao
from db import init_db
from main import create_app
from service import GameService


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def db_path(tmp_path) -> str:
    return str(tmp_path / "games.db")


@pytest.fixture
async def service(db_path):
    await init_db(db_path)
    async with aiosqlite.connect(db_path) as conn:
        yield GameService(GameDao(conn))


@pytest.fixture
def client(db_path):
    with TestClient(create_app(db_path)) as test_client:
        yield test_client
