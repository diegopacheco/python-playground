from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from library.db import make_engine, session_scope

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def db_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("LIBRARY_DB_URL", url)
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    return url


@pytest.fixture
def session(db_url: str) -> Iterator[Session]:
    with session_scope(make_engine(db_url)) as session:
        yield session
