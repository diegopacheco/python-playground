import asyncio
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from dao import AccountDAO, LedgerDAO
from service import (
    AccountNotFound,
    BankService,
    InsufficientFunds,
    InvalidTransfer,
    LedgerService,
)
from tx import (
    CrossTaskTransaction,
    NoActiveTransaction,
    TransactionNotYours,
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


async def test_missing_target_is_refused_before_any_row_is_written(
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
    source = await bank.open_account("alice", Decimal("100.00"))
    target = await bank.open_account("bob", Decimal("0.00"))
    ledger = LedgerService()

    await ledger.record(source.id, target.id, Decimal("5.00"))

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


async def test_a_cancelled_joined_call_cannot_commit_its_partial_work(bank: BankService):
    account = await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def slow_leg() -> None:
        await bank.deposit(account.id, Decimal("5.00"))
        await asyncio.sleep(5)

    @transactional
    async def caller() -> None:
        try:
            async with asyncio.timeout(0.05):
                await slow_leg()
        except TimeoutError:
            pass

    with pytest.raises(UnexpectedRollback):
        await caller()

    assert (await bank.get_account(account.id)).balance == Decimal("10.00")


async def test_a_swallowed_database_error_cannot_be_committed_over(bank: BankService):
    await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def caller() -> list:
        try:
            await bank.open_account("alice", Decimal("5.00"))
        except IntegrityError:
            pass
        return await bank.list_accounts()

    with pytest.raises(UnexpectedRollback):
        await caller()

    assert len(await bank.list_accounts()) == 1


async def test_a_spawned_task_cannot_borrow_the_callers_session(bank: BankService):
    @transactional
    async def caller() -> None:
        await asyncio.create_task(bank.list_accounts())

    with pytest.raises(CrossTaskTransaction):
        await caller()


async def test_a_transfer_to_the_same_account_is_rejected(bank: BankService):
    account = await bank.open_account("alice", Decimal("100.00"))

    with pytest.raises(InvalidTransfer):
        await bank.transfer(account.id, account.id, Decimal("30.00"))

    assert await bank.list_ledger() == []
    assert (await bank.get_account(account.id)).balance == Decimal("100.00")


async def test_the_ledger_cannot_reference_an_account_that_does_not_exist(
    bank: BankService,
):
    source = await bank.open_account("alice", Decimal("100.00"))
    ledger = LedgerService()

    with pytest.raises(IntegrityError):
        await ledger.record(source.id, 9999, Decimal("5.00"))

    assert await bank.list_ledger() == []


async def test_the_schema_refuses_a_negative_balance(bank: BankService):
    account = await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def force_overdraft() -> None:
        await current_session().execute(
            text("update accounts set balance = -1 where id = :id"), {"id": account.id}
        )

    with pytest.raises(IntegrityError):
        await force_overdraft()

    assert (await bank.get_account(account.id)).balance == Decimal("10.00")


async def test_a_swallowed_dao_error_cannot_be_reported_as_success(bank: BankService):
    """A database error caught straight off a DAO never passes through a @transactional
    frame, so nothing marks the transaction rollback-only. Postgres has already
    deactivated it, and committing a dead transaction is a silent no-op: without the
    liveness check the boundary returns success for work the database threw away."""
    await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def caller() -> str:
        await AccountDAO().insert("carol", Decimal("777.00"))
        try:
            await AccountDAO().insert("alice", Decimal("1.00"))
        except IntegrityError:
            pass
        return "the work is done"

    with pytest.raises(UnexpectedRollback):
        await caller()

    assert [account.owner for account in await bank.list_accounts()] == ["alice"]


async def test_business_code_cannot_commit_the_boundarys_transaction(bank: BankService):
    """current_session() is handed to every DAO. If it were the raw AsyncSession then
    any of them could commit, and the half of a transfer that ran before the commit
    would survive the rollback of the half that ran after it."""
    source = await bank.open_account("alice", Decimal("100.00"))
    target = await bank.open_account("bob", Decimal("0.00"))

    @transactional
    async def half_a_transfer() -> None:
        await bank.withdraw(source.id, Decimal("30.00"))
        await current_session().commit()
        await bank.deposit(target.id, Decimal("30.00"))

    with pytest.raises(TransactionNotYours):
        await half_a_transfer()

    assert (await bank.get_account(source.id)).balance == Decimal("100.00")
    assert (await bank.get_account(target.id)).balance == Decimal("0.00")


async def test_unexpected_rollback_names_the_exception_that_poisoned_it(
    bank: BankService,
):
    """The failure worth reporting is the one that made the transaction unusable, not
    whatever the caller happened to trip over afterwards. The later error stays
    reachable as __context__ so the traceback still shows both."""
    account = await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def caller() -> None:
        try:
            await bank.withdraw(account.id, Decimal("999.00"))
        except InsufficientFunds:
            pass
        await bank.get_account(4242)

    with pytest.raises(UnexpectedRollback) as failure:
        await caller()

    assert isinstance(failure.value.__cause__, InsufficientFunds)
    assert isinstance(failure.value.__context__, AccountNotFound)


async def test_a_lock_helper_cannot_hand_an_entity_across_a_boundary(bank: BankService):
    """lock_account returns an ORM entity, so it must never be a boundary of its own:
    it would close its session on the way out and hand the caller a detached row."""
    account = await bank.open_account("alice", Decimal("10.00"))

    with pytest.raises(NoActiveTransaction):
        await bank.lock_account(account.id)
