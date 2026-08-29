from decimal import Decimal

import pytest

from service import BankService, InvalidAmount


async def total_balance(bank: BankService) -> Decimal:
    return sum((a.balance for a in await bank.list_accounts()), Decimal("0.00"))


async def test_a_sub_cent_transfer_cannot_invent_money(bank: BankService):
    """Numeric(18, 2) rounds each leg on its own, so a debit of 0.125 and a credit of
    0.125 land as 0.12 and 0.13. Refusing the amount is what keeps the total constant."""
    source = await bank.open_account("alice", Decimal("100.00"))
    target = await bank.open_account("bob", Decimal("50.00"))
    before = await total_balance(bank)

    with pytest.raises(InvalidAmount):
        await bank.transfer(source.id, target.id, Decimal("0.125"))

    assert await total_balance(bank) == before
    assert await bank.list_ledger() == []


async def test_a_sub_cent_deposit_is_refused(bank: BankService):
    """0.005 rounds up to a cent the depositor never paid."""
    account = await bank.open_account("alice", Decimal("100.00"))

    with pytest.raises(InvalidAmount):
        await bank.deposit(account.id, Decimal("0.005"))

    assert (await bank.get_account(account.id)).balance == Decimal("100.00")


async def test_a_sub_cent_opening_balance_is_refused(bank: BankService):
    with pytest.raises(InvalidAmount):
        await bank.open_account("alice", Decimal("0.005"))

    assert await bank.list_accounts() == []


async def test_a_non_finite_amount_is_refused(bank: BankService):
    """Decimal('NaN') <= 0 raises InvalidOperation, so the guard has to run first or
    the caller gets a decimal error instead of a refusal."""
    account = await bank.open_account("alice", Decimal("100.00"))

    for amount in (Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")):
        with pytest.raises(InvalidAmount):
            await bank.deposit(account.id, amount)

    assert (await bank.get_account(account.id)).balance == Decimal("100.00")


async def test_an_amount_the_column_cannot_hold_is_refused(bank: BankService):
    """Numeric(18, 2) holds sixteen digits before the point; more is a DataError from
    Postgres, which is a 500 the caller cannot act on."""
    account = await bank.open_account("alice", Decimal("100.00"))

    with pytest.raises(InvalidAmount):
        await bank.deposit(account.id, Decimal("1e30"))

    assert (await bank.get_account(account.id)).balance == Decimal("100.00")


async def test_the_returned_view_is_the_value_the_database_kept(bank: BankService):
    """The view is built from the flushed entity, not from a re-read, so an amount that
    Postgres would store differently has to be refused before it reaches the column."""
    account = await bank.open_account("alice", Decimal("100.00"))

    returned = await bank.deposit(account.id, Decimal("0.1"))
    stored = await bank.get_account(account.id)

    assert returned.balance == stored.balance
    assert str(returned.balance) == str(stored.balance) == "100.10"
