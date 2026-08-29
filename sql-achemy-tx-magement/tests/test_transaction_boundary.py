import asyncio
from decimal import Decimal

import pytest

from dao import AccountDAO, LedgerDAO
from service import AccountNotFound, BankService, InsufficientFunds, LedgerService
from tx import (
    NoActiveTransaction,
    UnexpectedRollback,
    current_session,
    transactional,
)


async def test_committed_work_is_visible_to_the_next_transaction(bank: BankService):
    account = await bank.open_account("alice", Decimal("100.00"))

    await bank.deposit(account.id, Decimal("40.00"))

    reloaded = await bank.get_account(account.id)
    assert reloaded.balance == Decimal("140.00")


async def test_transfer_commits_both_legs_and_the_ledger_together(bank: BankService):
    source = await bank.open_account("alice", Decimal("100.00"))
    target = await bank.open_account("bob", Decimal("10.00"))

    await bank.transfer(source.id, target.id, Decimal("30.00"))

    assert (await bank.get_account(source.id)).balance == Decimal("70.00")
    assert (await bank.get_account(target.id)).balance == Decimal("40.00")
    assert len(await bank.list_ledger()) == 1


async def test_insufficient_funds_rolls_back_the_ledger_entry(bank: BankService):
    source = await bank.open_account("alice", Decimal("20.00"))
    target = await bank.open_account("bob", Decimal("10.00"))

    with pytest.raises(InsufficientFunds):
        await bank.transfer(source.id, target.id, Decimal("50.00"))

    assert await bank.list_ledger() == []
    assert (await bank.get_account(source.id)).balance == Decimal("20.00")
    assert (await bank.get_account(target.id)).balance == Decimal("10.00")


async def test_missing_target_rolls_back_the_ledger_row_already_inserted(
    bank: BankService,
):
    source = await bank.open_account("alice", Decimal("100.00"))

    with pytest.raises(AccountNotFound):
        await bank.transfer(source.id, 9999, Decimal("30.00"))

    assert (await bank.get_account(source.id)).balance == Decimal("100.00")
    assert await bank.list_ledger() == []


async def test_nested_service_calls_join_the_caller_transaction(
    bank: BankService, monkeypatch: pytest.MonkeyPatch
):
    seen = []
    original = AccountDAO.update_balance

    async def spy(self, account, balance):
        seen.append(current_session())
        return await original(self, account, balance)

    monkeypatch.setattr(AccountDAO, "update_balance", spy)
    source = await bank.open_account("alice", Decimal("100.00"))
    target = await bank.open_account("bob", Decimal("0.00"))

    await bank.transfer(source.id, target.id, Decimal("30.00"))

    assert len(seen) == 2
    assert seen[0] is seen[1]


async def test_separate_service_calls_get_separate_transactions(
    bank: BankService, monkeypatch: pytest.MonkeyPatch
):
    seen = []
    original = AccountDAO.update_balance

    async def spy(self, account, balance):
        seen.append(current_session())
        return await original(self, account, balance)

    monkeypatch.setattr(AccountDAO, "update_balance", spy)
    account = await bank.open_account("alice", Decimal("100.00"))

    await bank.deposit(account.id, Decimal("10.00"))
    await bank.deposit(account.id, Decimal("10.00"))

    assert seen[0] is not seen[1]


async def test_concurrent_transactions_do_not_share_a_session(
    bank: BankService, monkeypatch: pytest.MonkeyPatch
):
    seen = []
    original = AccountDAO.update_balance

    async def spy(self, account, balance):
        seen.append(current_session())
        await asyncio.sleep(0)
        return await original(self, account, balance)

    monkeypatch.setattr(AccountDAO, "update_balance", spy)
    alice = await bank.open_account("alice", Decimal("100.00"))
    bob = await bank.open_account("bob", Decimal("100.00"))

    await asyncio.gather(
        bank.deposit(alice.id, Decimal("5.00")),
        bank.deposit(bob.id, Decimal("7.00")),
    )

    assert len({id(session) for session in seen}) == 2
    assert (await bank.get_account(alice.id)).balance == Decimal("105.00")
    assert (await bank.get_account(bob.id)).balance == Decimal("107.00")


async def test_dao_access_without_a_transaction_is_rejected():
    with pytest.raises(NoActiveTransaction):
        await AccountDAO().find_all()


async def test_rollback_leaves_no_open_transaction_behind(bank: BankService):
    source = await bank.open_account("alice", Decimal("1.00"))

    with pytest.raises(InsufficientFunds):
        await bank.withdraw(source.id, Decimal("9.00"))

    await bank.deposit(source.id, Decimal("2.00"))
    assert (await bank.get_account(source.id)).balance == Decimal("3.00")


async def test_transaction_context_is_cleared_after_the_boundary_returns():
    @transactional
    async def inside():
        return current_session()

    session = await inside()
    assert session is not None
    with pytest.raises(NoActiveTransaction):
        current_session()


async def test_call_into_another_service_joins_the_same_transaction(
    bank: BankService, monkeypatch: pytest.MonkeyPatch
):
    seen = []
    original_insert = LedgerDAO.insert
    original_update = AccountDAO.update_balance

    async def spy_insert(self, source_id, target_id, amount):
        seen.append(current_session())
        return await original_insert(self, source_id, target_id, amount)

    async def spy_update(self, account, balance):
        seen.append(current_session())
        return await original_update(self, account, balance)

    monkeypatch.setattr(LedgerDAO, "insert", spy_insert)
    monkeypatch.setattr(AccountDAO, "update_balance", spy_update)
    source = await bank.open_account("alice", Decimal("100.00"))
    target = await bank.open_account("bob", Decimal("0.00"))

    await bank.transfer(source.id, target.id, Decimal("30.00"))

    assert len(seen) == 3
    assert seen[0] is seen[1] is seen[2]


async def test_the_other_service_opens_its_own_transaction_when_called_alone(
    bank: BankService,
):
    ledger = LedgerService()

    await ledger.record(1, 2, Decimal("5.00"))

    assert len(await bank.list_ledger()) == 1


async def test_a_failure_swallowed_by_the_caller_still_rolls_the_transaction_back(
    bank: BankService,
):
    account = await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def caller() -> None:
        try:
            await bank.withdraw(account.id, Decimal("999.00"))
        except InsufficientFunds:
            pass
        await bank.deposit(account.id, Decimal("5.00"))

    with pytest.raises(UnexpectedRollback):
        await caller()

    assert (await bank.get_account(account.id)).balance == Decimal("10.00")


async def test_rollback_only_does_not_leak_into_the_next_transaction(bank: BankService):
    account = await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def caller() -> None:
        try:
            await bank.withdraw(account.id, Decimal("999.00"))
        except InsufficientFunds:
            pass

    with pytest.raises(UnexpectedRollback):
        await caller()

    await bank.deposit(account.id, Decimal("5.00"))
    assert (await bank.get_account(account.id)).balance == Decimal("15.00")
