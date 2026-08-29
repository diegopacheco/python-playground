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
