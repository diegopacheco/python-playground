from decimal import Decimal

import pytest
from sqlalchemy import text

from models import Account
from service import BankService
from tx import UnexpectedRollback, current_session, transactional


@transactional
async def commit_before_the_latch_arms() -> None:
    session = current_session()
    session.add(Account(owner="ghost", balance=Decimal("10.00")))
    await session.execute(text("COMMIT"))


@transactional
async def rollback_before_the_latch_arms() -> None:
    session = current_session()
    session.add(Account(owner="ghost", balance=Decimal("10.00")))
    await session.execute(text("ROLLBACK"))


async def test_a_raw_commit_as_the_first_statement_is_still_caught():
    with pytest.raises(UnexpectedRollback):
        await commit_before_the_latch_arms()
    assert await BankService().list_accounts() == []


async def test_a_raw_rollback_as_the_first_statement_is_still_caught():
    with pytest.raises(UnexpectedRollback):
        await rollback_before_the_latch_arms()
    assert await BankService().list_accounts() == []
