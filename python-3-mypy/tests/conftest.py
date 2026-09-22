from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from library.db import make_engine, make_session_factory

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def db_url(tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def migrated(db_url: str) -> str:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", db_url)
    config.attributes["sqlalchemy.url"] = db_url
    command.upgrade(config, "head")
    return db_url


@pytest.fixture
def session(migrated: str) -> Iterator[Session]:
    factory = make_session_factory(make_engine(migrated))
    with factory() as s:
        yield s
