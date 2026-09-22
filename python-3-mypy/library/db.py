import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_URL = "sqlite:///library.db"


def database_url() -> str:
    return os.environ.get("LIBRARY_DB_URL", DEFAULT_URL)


def make_engine(url: str | None = None) -> Engine:
    return create_engine(url or database_url())


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
