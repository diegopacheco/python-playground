import os

os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://bank_user:bank_pass@localhost:5434/bank_test_db",
)

import pytest
from sqlalchemy import text

from db import create_schema, engine
from service import BankService
from tx import current_session, transactional


@transactional
async def truncate_all() -> None:
    await current_session().execute(
        text("TRUNCATE accounts, ledger RESTART IDENTITY")
    )


@pytest.fixture(autouse=True)
async def database():
    await create_schema()
    await truncate_all()
    yield
    await engine.dispose()


@pytest.fixture
def bank() -> BankService:
    return BankService()
