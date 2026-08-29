import os

os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://bank_user:bank_pass@localhost:5434/bank_test_db",
)

import psycopg
import pytest

from db import Base, engine
from service import BankService

ONE_RUN_AT_A_TIME = 8148213
CONCURRENT_RUNS = (
    "another pytest run is already using this database. The suite drops and recreates "
    "the schema before every test, so two runs at once delete each other's rows and "
    "fail in ways that read as bugs in the boundary. Wait for the other run, or point "
    "TEST_DATABASE_URL at a database of your own."
)

_only_run = psycopg.connect(
    os.environ["DATABASE_URL"].replace("+psycopg", ""), autocommit=True
)
if not _only_run.execute(
    "select pg_try_advisory_lock(%s)", (ONE_RUN_AT_A_TIME,)
).fetchone()[0]:
    raise RuntimeError(CONCURRENT_RUNS)


@pytest.fixture(autouse=True)
async def database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest.fixture
def bank() -> BankService:
    return BankService()
