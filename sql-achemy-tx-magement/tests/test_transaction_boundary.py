import asyncio
import copy
import inspect
import pickle
from decimal import Decimal
from typing import Any
from weakref import ReferenceType

import pytest
from sqlalchemy import Connection, Engine, select, text
from sqlalchemy.engine import Transaction
from sqlalchemy.exc import (
    ArgumentError,
    DBAPIError,
    IntegrityError,
    InvalidRequestError,
    OperationalError,
    ProgrammingError,
)
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_object_session,
)
from sqlalchemy.orm import Session, SessionTransaction
from sqlalchemy.util import greenlet_spawn

from dao import AccountDAO, LedgerDAO
from db import engine
from models import Account
from service import (
    AccountNotFound,
    AccountView,
    BankService,
    InsufficientFunds,
    InvalidOwner,
    InvalidTransfer,
    LedgerService,
    _lock_accounts,
)
from tx import (
    DISCARDED_BY_POSTGRES,
    LOST_MARK,
    BoundarySession,
    _held_by,
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


async def test_the_ledger_refuses_an_account_that_does_not_exist(bank: BankService):
    """record() is a boundary of its own, so the lock it takes has to prove both
    accounts exist the way transfer() does. Leaving that to the foreign key turned a
    missing account into an IntegrityError, which the controller reports as a 409
    conflict for a row that was never there."""
    source = await bank.open_account("alice", Decimal("100.00"))
    ledger = LedgerService()

    with pytest.raises(AccountNotFound):
        await ledger.record(source.id, 9999, Decimal("5.00"))

    assert await bank.list_ledger() == []


async def test_the_schema_refuses_an_orphan_ledger_row(bank: BankService):
    """The service check is the first net, not the only one. The foreign key is what
    stops a bug that reaches the DAO directly from leaving an orphan behind."""
    source = await bank.open_account("alice", Decimal("100.00"))

    @transactional
    async def write_an_orphan() -> None:
        await LedgerDAO().insert(source.id, 9999, Decimal("5.00"))

    with pytest.raises(IntegrityError):
        await write_an_orphan()

    assert await bank.list_ledger() == []


async def test_the_schema_refuses_a_ledger_amount_that_is_not_money(
    bank: BankService,
):
    """`balance` has a backstop for a service bug and `amount` had none, so the two
    halves of a transfer were not held to the same standard: a bug that wrote a
    negative row moved money one way and recorded it the other. The `NaN` half is the
    same argument that put it on `balance` - postgres orders `NaN` above every number,
    so `amount > 0` is true for one and the check that looks like it covers the column
    would not."""
    source = await bank.open_account("alice", Decimal("100.00"))
    target = await bank.open_account("bob", Decimal("100.00"))

    @transactional
    async def write_it(amount: Decimal) -> None:
        await LedgerDAO().insert(source.id, target.id, amount)

    for amount in (Decimal("-5.00"), Decimal("0.00"), Decimal("NaN")):
        with pytest.raises(IntegrityError):
            await write_it(amount)

    assert await bank.list_ledger() == []


async def test_the_schema_refuses_a_ledger_row_that_moves_nothing(bank: BankService):
    """`_check_transfer` refuses a row saying an account paid itself, and the database
    is where that has to hold for a bug that reaches the DAO directly - the foreign
    keys are both satisfied by a self-transfer, so nothing else in the schema sees it."""
    account = await bank.open_account("alice", Decimal("100.00"))

    @transactional
    async def pay_itself() -> None:
        await LedgerDAO().insert(account.id, account.id, Decimal("5.00"))

    with pytest.raises(IntegrityError):
        await pay_itself()

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


async def test_a_swallowed_select_error_cannot_be_reported_as_success(
    bank: BankService,
):
    """SQLAlchemy only deactivates its SessionTransaction on a failed flush. A statement
    error from any other call leaves is_active True while Postgres has already aborted
    the transaction, so the liveness check alone passes and the COMMIT that follows is a
    silent no-op. The session itself has to record the failure."""
    @transactional
    async def caller() -> str:
        await AccountDAO().insert("carol", Decimal("777.00"))
        try:
            await current_session().execute(text("select * from no_such_table"))
        except ProgrammingError:
            pass
        return "the work is done"

    with pytest.raises(UnexpectedRollback) as failure:
        await caller()

    assert isinstance(failure.value.__cause__, ProgrammingError)
    assert await bank.list_accounts() == []


async def test_a_thread_inside_a_boundary_cannot_borrow_the_session(bank: BankService):
    """asyncio.to_thread copies the context into the worker thread, so the session is
    reachable there. There is no running loop in that thread, and asking for the current
    task raises, so the guard has to answer 'no task' rather than let a RuntimeError
    about the event loop stand in for the real refusal."""
    @transactional
    async def caller() -> None:
        await asyncio.to_thread(current_session)

    with pytest.raises(CrossTaskTransaction):
        await caller()


async def test_a_session_captured_inside_a_boundary_is_dead_outside_it(
    bank: BankService,
):
    """An AsyncSession autobegins on next use, so a BoundarySession kept past its
    boundary would quietly open a second transaction that nothing can ever commit."""
    @transactional
    async def capture():
        return current_session()

    session = await capture()

    with pytest.raises(NoActiveTransaction):
        await session.execute(text("select 1"))


async def test_a_streamed_error_cannot_be_committed_over(bank: BankService):
    """stream() opens a server-side cursor, so the statement fails while the result is
    iterated rather than inside a session call the boundary wraps. Nothing records the
    DBAPIError, SQLAlchemy still reports is_active true, and a caller who swallows it
    gets success for work Postgres threw away. The boundary refuses the method instead."""
    @transactional
    async def caller() -> None:
        await current_session().stream(text("select 1"))

    with pytest.raises(TransactionNotYours):
        await caller()

    @transactional
    async def scalars_caller() -> None:
        await current_session().stream_scalars(text("select 1"))

    with pytest.raises(TransactionNotYours):
        await scalars_caller()


async def test_a_transaction_ended_behind_the_boundarys_back_is_not_a_commit(
    bank: BankService,
):
    """The liveness check is the net for a transaction that ended without any DBAPIError
    to record. Reaching past the wrapper to end it leaves nothing to commit, and the
    boundary has to say so instead of returning success."""
    await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def caller() -> str:
        await AccountDAO().insert("carol", Decimal("777.00"))
        await _held_by(current_session())[0].rollback()
        return "the work is done"

    with pytest.raises(UnexpectedRollback):
        await caller()

    assert [account.owner for account in await bank.list_accounts()] == ["alice"]


async def test_both_accounts_are_locked_in_ascending_id_order(bank: BankService):
    """Two transfers in opposite directions only queue safely if both take the row locks
    in the same order. Postgres locks in the order the scan produces rows, which is heap
    order, and a non-HOT update moves a row's tuple: owner is indexed, so renaming the
    lower id puts it physically after the higher one. ORDER BY id is what survives that."""
    low = await bank.open_account("alice", Decimal("100.00"))
    high = await bank.open_account("bob", Decimal("100.00"))

    @transactional
    async def reorder_the_heap() -> list[int]:
        session = current_session()
        await session.execute(
            text("update accounts set owner = 'moved' where id = :id"), {"id": low.id}
        )
        unordered = await session.execute(
            text("select id from accounts where id in (:a, :b) for update"),
            {"a": low.id, "b": high.id},
        )
        return list(unordered.scalars())

    assert await reorder_the_heap() == [high.id, low.id], "heap order is still id order"

    @transactional
    async def locked() -> list[int]:
        return [a.id for a in await AccountDAO().find_all_for_update([high.id, low.id])]

    assert await locked() == [low.id, high.id]


async def test_business_code_cannot_reach_the_sync_session_and_commit(
    bank: BankService,
):
    """run_sync() hands out the very Session that sync_session is refused for, so
    leaving it open blocked nothing. A commit through it committed the debit leg of a
    transfer, the boundary rolled back the credit leg it could still see, and thirty
    units of money stopped existing."""
    source = await bank.open_account("alice", Decimal("100.00"))
    target = await bank.open_account("bob", Decimal("0.00"))

    @transactional
    async def half_a_transfer() -> None:
        await bank.withdraw(source.id, Decimal("30.00"))
        await current_session().run_sync(lambda session: session.commit())
        await bank.deposit(target.id, Decimal("30.00"))

    with pytest.raises(TransactionNotYours):
        await half_a_transfer()

    assert (await bank.get_account(source.id)).balance == Decimal("100.00")
    assert (await bank.get_account(target.id)).balance == Decimal("0.00")


async def test_every_way_of_ending_the_transaction_is_refused(bank: BankService):
    """close() and aclose() were refused while reset(), invalidate() and close_all()
    ended the same transaction the same way. The liveness check caught them, but a
    refusal that names the call is the answer the caller can act on. The rest reach
    past the boundary rather than ending it: _proxied and _proxy_objects are two more
    names for the sync Session, get_bind and bind are two names for the engine, and
    identity_map is the session's own state under a name that is not a method.
    get_nested_transaction is on the list for the same reason get_transaction is: it
    hands out a SessionTransaction that can be ended directly. It only ever answers
    None while begin_nested is refused, which is precisely why an audit that stops at
    what is reachable today would have left it off."""
    for name in (
        "reset",
        "invalidate",
        "close_all",
        "run_sync",
        "sync_session",
        "_proxied",
        "_proxy_objects",
        "get_bind",
        "bind",
        "identity_map",
        "get_nested_transaction",
    ):

        @transactional
        async def caller(name=name) -> None:
            getattr(current_session(), name)

        with pytest.raises(TransactionNotYours):
            await caller()


async def test_a_swallowed_cancellation_at_the_session_cannot_be_committed_over(
    bank: BankService,
):
    """A cancelled statement leaves the connection unusable without ever raising a
    DBAPIError, and it never crosses a @transactional frame when the DAO call is
    awaited directly. Unrecorded, the boundary reached COMMIT and failed there with a
    SQLAlchemy state error instead of naming what went wrong."""
    await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def caller() -> str:
        await AccountDAO().insert("carol", Decimal("777.00"))
        try:
            async with asyncio.timeout(0.05):
                await current_session().execute(text("select pg_sleep(3)"))
        except TimeoutError:
            pass
        return "the work is done"

    with pytest.raises(UnexpectedRollback) as failure:
        await caller()

    assert isinstance(failure.value.__cause__, asyncio.CancelledError)
    assert [account.owner for account in await bank.list_accounts()] == ["alice"]


async def test_transactional_refuses_a_function_that_is_not_async():
    """The wrapper awaits what it wraps, so a sync function failed at call time with
    a TypeError about the return value rather than at the decorator that is wrong."""
    with pytest.raises(TypeError):

        @transactional
        def not_async() -> int:
            return 1


async def test_a_captured_session_cannot_be_driven_from_a_spawned_task(bank: BankService):
    """current_session() refuses a spawned task, but the wrapper it hands back travels.
    Capturing it inside the boundary and using the object from a task got past the
    lookup entirely, so the check has to live on the object as well as on the lookup."""

    @transactional
    async def caller() -> int:
        session = current_session()

        async def spawned() -> int:
            result = await session.execute(text("select 1"))
            return result.scalar_one()

        return await asyncio.create_task(spawned())

    with pytest.raises(CrossTaskTransaction):
        await caller()


async def test_a_spawned_task_cannot_write_through_a_captured_session(bank: BankService):
    """The read is the symptom; this is the damage. The spawned task's INSERT used to
    be committed by a boundary that never saw it, while the same task calling any
    @transactional method or current_session() was refused."""

    @transactional
    async def caller() -> None:
        session = current_session()

        async def spawned() -> None:
            await session.execute(
                text("insert into accounts (owner, balance) values ('ghost', 1.00)")
            )

        await asyncio.create_task(spawned())

    with pytest.raises(CrossTaskTransaction):
        await caller()

    assert await bank.list_accounts() == []


async def test_a_captured_session_cannot_be_driven_from_a_thread(bank: BankService):
    """asyncio.to_thread copies the context, and the wrapper can simply be closed over.
    The worker has no running loop, so the task lookup answers 'no task' and the
    refusal is the same one a spawned task gets."""

    @transactional
    async def caller() -> None:
        session = current_session()
        await asyncio.to_thread(lambda: session.add(Account(owner="ghost", balance=1)))

    with pytest.raises(CrossTaskTransaction):
        await caller()


async def test_the_three_names_for_the_sync_session_are_all_refused(bank: BankService):
    """sync_session, run_sync and _proxied are the same object. Blocking two of them
    left the third open, and a commit through it splits the boundary the same way."""

    @transactional
    async def same_object() -> bool:
        session = current_session()
        return _held_by(session)[0]._proxied is _held_by(session)[0].sync_session

    assert await same_object() is True

    for name in ("sync_session", "run_sync", "_proxied"):

        @transactional
        async def caller(name=name) -> None:
            getattr(current_session(), name)

        with pytest.raises(TransactionNotYours):
            await caller()


async def test_the_stream_refusal_cannot_be_routed_around_through_execute(
    bank: BankService,
):
    """stream() is refused because a server-side cursor fails where the boundary
    cannot see it. execute(stream_results=True) asks for the same cursor, so the
    refusal is only worth anything if that route is closed too. The DECLARE does reach
    Postgres, but SQLAlchemy closes the cursor and raises before a row is read, so the
    transaction survives and the work either side of it still commits."""
    swallowed = []

    @transactional
    async def caller() -> str:
        await AccountDAO().insert("carol", Decimal("777.00"))
        try:
            await current_session().execute(
                select(Account).execution_options(stream_results=True)
            )
        except InvalidRequestError as error:
            swallowed.append(error)
        return "the work is done"

    assert await caller() == "the work is done"
    assert len(swallowed) == 1
    assert [account.owner for account in await bank.list_accounts()] == ["carol"]


async def test_a_missing_account_is_refused_even_when_the_ids_are_a_generator(
    bank: BankService,
):
    """_lock_accounts takes an Iterable and used to walk it twice: find_all_for_update
    consumed it into a set, and the existence check that follows then found nothing to
    check. A generator silently turned AccountNotFound into a foreign key violation,
    which the controller reports as a 409 over a row that was never there."""

    @transactional
    async def caller() -> list:
        return await _lock_accounts(AccountDAO(), (account_id for account_id in (4242,)))

    with pytest.raises(AccountNotFound):
        await caller()


async def test_a_captured_session_method_cannot_be_driven_from_a_spawned_task(
    bank: BankService,
):
    """Checking the task on the way through __getattr__ guards the object, not the use.
    A bound method taken off the session inside the boundary carried no check at all, so
    capturing execute instead of the session got a spawned task straight back in."""

    @transactional
    async def caller() -> int:
        execute = current_session().execute

        async def spawned() -> int:
            result = await execute(text("select 1"))
            return result.scalar_one()

        return await asyncio.create_task(spawned())

    with pytest.raises(CrossTaskTransaction):
        await caller()


async def test_a_spawned_task_cannot_write_through_a_captured_method(bank: BankService):
    """The damage the read only hints at. The spawned task's INSERT went through a
    method the boundary had already handed out, so nothing refused it and the boundary
    committed a row it never saw."""

    @transactional
    async def caller() -> None:
        execute = current_session().execute

        async def spawned() -> None:
            await execute(
                text("insert into accounts (owner, balance) values ('ghost', 1.00)")
            )

        await asyncio.create_task(spawned())

    with pytest.raises(CrossTaskTransaction):
        await caller()

    assert await bank.list_accounts() == []


async def test_a_captured_sync_method_cannot_be_driven_from_a_thread(bank: BankService):
    """add() is not a coroutine function, so it used to be handed back unwrapped and
    was the one call with no guard on it in any form. A worker thread staged an entity
    through it and the boundary flushed and committed the row."""

    @transactional
    async def caller() -> None:
        add = current_session().add
        await asyncio.to_thread(lambda: add(Account(owner="ghost", balance=1)))

    with pytest.raises(CrossTaskTransaction):
        await caller()

    assert await bank.list_accounts() == []


async def test_a_captured_method_is_dead_outside_its_boundary(bank: BankService):
    """The session goes dead with the boundary; so must anything taken off it. A
    captured method autobegan a second transaction on a closed session, which checked a
    connection out of the pool that nothing ever returned: one leak per call, until the
    pool is empty and every request is a 503."""
    holder = {}

    @transactional
    async def capture() -> None:
        holder["execute"] = current_session().execute

    await capture()

    with pytest.raises(NoActiveTransaction):
        await holder["execute"](text("select 1"))


async def test_two_session_calls_cannot_be_gathered(bank: BankService):
    """The realistic shape of the mistake: parallelise two queries on the session you
    already hold. gather() awaits both coroutines in child tasks, so the guard has to
    run when the coroutine is stepped and not only when the method is looked up. It
    used to surface as IllegalStateChangeError raised out of session teardown, which is
    an unhandled 500 and another connection left behind in INTRANS."""

    @transactional
    async def caller() -> None:
        session = current_session()
        await asyncio.gather(
            session.execute(text("select 1")), session.execute(text("select 2"))
        )

    with pytest.raises(CrossTaskTransaction):
        await caller()


async def test_object_session_is_a_fourth_name_for_the_sync_session(bank: BankService):
    """sync_session, run_sync and _proxied were refused while object_session handed the
    same Session back from any entity the DAOs had loaded. SQLAlchemy happens to refuse
    a sync commit made from a running loop, but a block list that is exhaustive by
    argument has to be exhaustive in fact."""
    account = await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def same_object() -> bool:
        entity = await AccountDAO().find(account.id)
        session = _held_by(current_session())[0]
        return session.object_session(entity) is session.sync_session

    assert await same_object() is True

    @transactional
    async def caller() -> None:
        getattr(current_session(), "object_session")

    with pytest.raises(TransactionNotYours):
        await caller()


async def test_a_server_side_cursor_asked_for_by_yield_per_is_refused_too(
    bank: BankService,
):
    """yield_per implies stream_results, so it is the same server-side cursor stream()
    is refused for. SQLAlchemy closes the cursor and raises before the rows are read,
    which is why the work either side of it still commits."""

    @transactional
    async def caller() -> str:
        await AccountDAO().insert("carol", Decimal("777.00"))
        try:
            await current_session().execute(
                select(Account).execution_options(yield_per=1)
            )
        except InvalidRequestError:
            pass
        return "the work is done"

    assert await caller() == "the work is done"
    assert [account.owner for account in await bank.list_accounts()] == ["carol"]


async def test_a_database_error_that_never_reached_postgres_is_still_poison(
    bank: BankService,
):
    """psycopg raises a DBAPIError for a parameter it cannot adapt, before anything is
    sent, so that one transaction really was still committable. The recorder poisons it
    anyway: telling the two apart means asking the driver whether the statement left the
    process, and a transaction manager that guesses wrong in the other direction reports
    success for discarded work. Erring towards the rollback is the decision."""

    @transactional
    async def caller() -> str:
        await AccountDAO().insert("carol", Decimal("777.00"))
        try:
            await current_session().execute(text("select :x"), {"x": object()})
        except ProgrammingError:
            pass
        return "the work is done"

    with pytest.raises(UnexpectedRollback):
        await caller()

    assert await bank.list_accounts() == []


async def test_the_engine_is_refused_under_both_of_its_names(bank: BankService):
    """get_bind() is refused because it hands out the engine, and `bind` is that same
    engine under a name that is not a method. It is set on the instance, so it never
    appears in dir(AsyncSession) and an audit of the class misses it. What comes back
    is the application's own engine, so a write made through it runs on a second
    connection, commits itself, and survives the rollback the boundary performs."""

    @transactional
    async def what_bind_hands_back() -> bool:
        return _held_by(current_session())[0].bind is engine

    assert await what_bind_hands_back() is True

    for name in ("bind", "get_bind"):

        @transactional
        async def caller(name=name) -> None:
            getattr(current_session(), name)

        with pytest.raises(TransactionNotYours):
            await caller()


async def test_the_proxy_registry_is_a_fifth_name_for_the_sync_session(
    bank: BankService,
):
    """sync_session, run_sync, _proxied and object_session were refused while
    _proxy_objects, the registry AsyncSession keeps so it can map a sync Session back
    to its async wrapper, handed the same Session out through a weakref. A commit
    through it happens to fail with MissingGreenlet, which is the accident
    object_session is already refused rather than relying on."""

    @transactional
    async def the_registry_holds_it() -> bool:
        raw = _held_by(current_session())[0]
        return any(ref() is raw.sync_session for ref in raw._proxy_objects)

    assert await the_registry_holds_it() is True

    @transactional
    async def caller() -> None:
        getattr(current_session(), "_proxy_objects")

    with pytest.raises(TransactionNotYours):
        await caller()


async def test_the_identity_map_is_not_handed_out(bank: BankService):
    """A callable is re-checked inside every call, but a non-callable is the value
    itself and no later check can reach it. identity_map is the session's live internal
    mapping, so handing it out hands out the session under a name the guard cannot
    follow: it crosses into a spawned task or a worker thread with nothing left to
    refuse it, and every entity the DAOs have loaded comes with it."""
    account = await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def the_map_is_live() -> bool:
        entity = await AccountDAO().find(account.id)
        held = _held_by(current_session())[0].identity_map.values()
        return any(loaded is entity for loaded in held)

    assert await the_map_is_live() is True

    @transactional
    async def caller() -> None:
        getattr(current_session(), "identity_map")

    with pytest.raises(TransactionNotYours):
        await caller()


async def test_a_context_manager_attribute_is_not_turned_into_a_function(
    bank: BankService,
):
    """The wrapper guarded anything callable, and a @contextmanager object is callable
    because it doubles as a decorator. no_autoflush therefore came back as a plain
    function with no __enter__, and `with current_session().no_autoflush:` was a
    TypeError: the wrapper silently broke a session API instead of guarding it or
    refusing it. Only routines are wrapped now, so the block below suppresses the
    flush it is supposed to suppress."""
    await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def rows_seen() -> tuple[int, int]:
        session = current_session()
        session.add(Account(owner="carol", balance=Decimal("1.00")))
        with session.no_autoflush:
            held_back = await session.execute(select(Account))
            inside = len(held_back.scalars().all())
        flushed = await session.execute(select(Account))
        return inside, len(flushed.scalars().all())

    assert await rows_seen() == (1, 2)


async def test_no_name_on_the_wrapper_hands_back_the_engine_or_the_sync_session(
    bank: BankService,
):
    """A block list is only as good as the audit that wrote it, and `bind` was missed
    because it is an instance attribute that never shows up in dir(AsyncSession). This
    walks every name the session actually has and fails on any that still hands back an
    engine or the sync Session, including through the weakrefs and dicts that
    _proxy_objects hid one behind. The connection under the session and the transaction
    object on it are escapes of the same kind - a commit through either one splits the
    boundary - so the sweep fails on those too."""

    def targets(value: Any) -> list[Any]:
        if isinstance(value, dict):
            value = list(value) + list(value.values())
        if not isinstance(value, list):
            value = [value]
        return [held() if isinstance(held, ReferenceType) else held for held in value]

    def frames(value: Any) -> list[Any]:
        try:
            frame = getattr(getattr(value, "gen", None), "gi_frame", None)
        except TransactionNotYours:
            return []
        return [] if frame is None else list(frame.f_locals.values())

    def entered(value: Any) -> list[Any]:
        if not (hasattr(type(value), "__enter__") and hasattr(type(value), "__exit__")):
            return []
        with value as inside:
            return [inside]

    @transactional
    async def sweep() -> list[str]:
        wrapper = current_session()
        escapes = (
            Engine,
            AsyncEngine,
            Session,
            AsyncSession,
            Connection,
            AsyncConnection,
            Transaction,
            SessionTransaction,
        )
        leaked = []
        for name in dir(wrapper):
            if name.startswith("__"):
                continue
            try:
                value = getattr(wrapper, name)
            except (TransactionNotYours, AttributeError):
                continue
            held = targets(value) + frames(value) + entered(value)
            if any(isinstance(one, escapes) for one in held):
                leaked.append(name)
        return leaked

    assert await sweep() == []


async def test_a_blank_owner_is_refused(bank: BankService):
    """min_length on the request model refuses the empty string and accepts a string of
    spaces, which is an account nobody can name. The service is the layer that has to
    know that, the same way it re-checks the amount the model has already parsed."""
    with pytest.raises(InvalidOwner):
        await bank.open_account("   ", Decimal("10.00"))

    assert await bank.list_accounts() == []


async def test_an_assignment_lands_on_the_session_and_not_on_the_wrapper(
    bank: BankService,
):
    """__getattr__ guarded every read and nothing guarded a write, so
    `current_session().autoflush = False` set the attribute on the wrapper and never
    reached the session. An instance attribute then shadows __getattr__, so reading it
    back returned the value that had not been applied: the wrapper reported the setting
    while the session went on flushing. Silently changing what a call means is the one
    thing this design is not allowed to do, and an assignment is a call."""
    await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def rows_seen() -> tuple[bool, int]:
        session = current_session()
        session.autoflush = False
        session.add(Account(owner="carol", balance=Decimal("1.00")))
        held_back = await session.execute(select(Account))
        return session.autoflush, len(held_back.scalars().all())

    assert await rows_seen() == (False, 1)


async def test_an_assignment_cannot_switch_the_block_list_off(bank: BankService):
    """The sharp half of the same hole. `current_session().bind = ...` used to succeed
    and put a value in the wrapper's own __dict__, which shadows __getattr__ entirely,
    so the very next read of `bind` handed back the assigned value instead of raising.
    An assignment could turn the refusal off, which makes the block list only as strong
    as the code that never assigns to it."""

    @transactional
    async def caller(name: str) -> None:
        setattr(current_session(), name, "not the boundary's to replace")

    for name in ("bind", "commit", "sync_session", "stream"):
        with pytest.raises(TransactionNotYours):
            await caller(name)

    @transactional
    async def still_refused() -> None:
        current_session().bind

    with pytest.raises(TransactionNotYours):
        await still_refused()


async def test_an_assignment_is_refused_from_a_spawned_task(bank: BankService):
    """Assignment takes the same two refusals every other route takes. Without the
    guard, a spawned task could stage work on the session through a setting rather than
    through a call, which is the one shape the task check on the lookup never saw."""

    @transactional
    async def caller() -> None:
        session = current_session()

        def off() -> None:
            session.autoflush = False

        await asyncio.to_thread(off)

    with pytest.raises(CrossTaskTransaction):
        await caller()


async def test_the_sessions_own_context_manager_is_refused(bank: BankService):
    """`async with session:` closes the session on the way out, which is close() under
    a syntax the block list cannot see: Python looks __aenter__ up on the type, so the
    name check never runs. It was already impossible, but only by accident, as a
    TypeError about a missing __aexit__ rather than an answer the caller can act on."""

    @transactional
    async def caller() -> None:
        async with current_session():
            pass

    with pytest.raises(TransactionNotYours):
        await caller()


async def test_the_result_object_hands_back_the_connection_under_the_boundary(
    bank: BankService,
):
    """The block list can only name what lives on the session, and this does not: the
    CursorResult that execute() hands back exposes the very Connection the boundary is
    holding, and the engine behind it. Refusing it would mean proxying every result and
    everything a result hands back, which is the cost that got stream() refused. It is
    pinned here so the limit is a fact the suite states rather than only prose."""

    @transactional
    async def what_a_result_carries() -> tuple[bool, bool]:
        result = await current_session().execute(text("select 1"))
        return (
            isinstance(result.connection, Connection),
            result.connection.engine is engine.sync_engine,
        )

    assert await what_a_result_carries() == (True, True)


async def test_a_commit_through_the_result_object_is_not_a_commit(bank: BankService):
    """Reaching the connection is one thing; the boundary reporting success over it is
    another. A commit through it split a transfer, and SQLAlchemy's SessionTransaction
    still reports is_active true afterwards, so the liveness check saw nothing and the
    boundary failed at COMMIT with a raw InvalidRequestError. The connection knows what
    the session does not, so the boundary asks it and names the answer."""
    source = await bank.open_account("alice", Decimal("100.00"))
    target = await bank.open_account("bob", Decimal("0.00"))

    @transactional
    async def half_a_transfer() -> str:
        await bank.withdraw(source.id, Decimal("30.00"))
        result = await current_session().execute(text("select 1"))
        await AsyncConnection._retrieve_proxy_for_target(result.connection).commit()
        return "the work is done"

    with pytest.raises(UnexpectedRollback):
        await half_a_transfer()

    assert (await bank.get_account(target.id)).balance == Decimal("0.00")


async def test_a_rollback_through_the_result_object_is_not_a_commit(bank: BankService):
    """The same route in the other direction, and the worse one: everything the
    boundary did is gone and there is no failure anywhere for it to notice."""

    @transactional
    async def caller() -> str:
        await AccountDAO().insert("carol", Decimal("777.00"))
        result = await current_session().execute(text("select 1"))
        await AsyncConnection._retrieve_proxy_for_target(result.connection).rollback()
        return "the work is done"

    with pytest.raises(UnexpectedRollback):
        await caller()

    assert await bank.list_accounts() == []


async def test_a_raw_rollback_string_is_caught_by_the_driver(bank: BankService):
    """This one used to get away. A ROLLBACK string ends the transaction inside
    Postgres, where neither SQLAlchemy's SessionTransaction nor its Connection is told:
    is_active stays true, in_transaction() stays true, the transaction object is still
    the one the boundary recorded, and all three of those nets pass over work the
    database threw away. psycopg was told, because libpq tracks the transaction status
    of the socket, so the fourth net asks the driver instead of asking SQLAlchemy about
    the driver."""

    @transactional
    async def caller() -> str:
        await AccountDAO().insert("carol", Decimal("777.00"))
        await current_session().execute(text("rollback"))
        return "the work is done"

    with pytest.raises(UnexpectedRollback) as refused:
        await caller()

    assert "postgres is no longer in the transaction" in str(refused.value)
    assert await bank.list_accounts() == []


async def test_a_raw_commit_string_is_caught_by_the_driver(bank: BankService):
    """The same route in the direction that keeps the first half instead of losing it,
    and the one three nets were blindest to: after a COMMIT string psycopg opens a
    fresh transaction for the next statement, so the boundary went on writing and
    committed the second half over a first half it no longer owned."""

    @transactional
    async def caller() -> str:
        await AccountDAO().insert("carol", Decimal("777.00"))
        await current_session().execute(text("commit"))
        await AccountDAO().insert("dave", Decimal("888.00"))
        return "the work is done"

    with pytest.raises(UnexpectedRollback):
        await caller()

    assert [account.owner for account in await bank.list_accounts()] == ["carol"]


async def test_a_commit_through_the_driver_under_the_result_is_not_a_commit(
    bank: BankService,
):
    """The result object carries the Connection, the Connection carries the pooled
    connection and that carries psycopg's own. A commit made down there is invisible to
    every SQLAlchemy object above it - the transaction the boundary recorded is still
    the transaction the Connection reports - which is the same blindness the raw string
    exploits and the same net that answers for it."""

    @transactional
    async def split_under_the_boundary() -> str:
        await AccountDAO().insert("carol", Decimal("777.00"))
        result = await current_session().execute(text("select 1"))
        await greenlet_spawn(result.connection.connection.dbapi_connection.commit)
        await AccountDAO().insert("dave", Decimal("888.00"))
        return "the work is done"

    with pytest.raises(UnexpectedRollback):
        await split_under_the_boundary()

    assert [account.owner for account in await bank.list_accounts()] == ["carol"]


async def test_a_write_on_a_second_connection_is_the_limit_that_stays(
    bank: BankService,
):
    """The engine behind the result is a way out of the boundary rather than a way to
    end it. A second connection opened from it commits itself, on a socket the boundary
    never held, so no net here can see it: the transaction the boundary owns is intact
    and postgres says so. A suite that only showed what is caught would leave the
    reader thinking the guarantee is absolute."""

    @transactional
    async def write_beside_the_boundary() -> str:
        result = await current_session().execute(text("select 1"))
        beside = AsyncEngine(result.connection.engine)
        async with beside.begin() as connection:
            await connection.execute(
                text("insert into accounts (owner, balance) values ('mallory', 1.00)")
            )
        await AccountDAO().insert("carol", Decimal("777.00"))
        raise InsufficientFunds("everything the boundary owns is rolled back")

    with pytest.raises(InsufficientFunds):
        await write_beside_the_boundary()

    assert [account.owner for account in await bank.list_accounts()] == ["mallory"]


async def test_a_boundary_marks_its_transaction_before_the_code_inside_it_runs(
    bank: BankService,
):
    """The mark used to go on at the first async call the business code made, so a
    boundary that had only staged work had no connection, no transaction identity and no
    mark: three of the five nets were switched off for as long as nobody awaited
    anything. That is not an exotic state. session.add() is a sync call, and an entity
    it has staged carries the AsyncSession, which SQLAlchemy hands back through its own
    async_object_session() - so a COMMIT sent by hand landed on a transaction the
    boundary was not watching and the rows it made durable survived the rollback that
    followed. The mark goes on the way in instead. It costs a connection and one SET
    LOCAL to a boundary that refuses a request before it reads anything, and it buys
    five nets that are armed for every line of code inside."""
    await engine.dispose()

    @transactional
    async def touches_nothing() -> str:
        current_session()
        return "no query was made"

    assert await touches_nothing() == "no query was made"
    assert engine.pool.checkedin() == 1

    @transactional
    async def what_the_transaction_is_marked_with() -> str:
        result = await current_session().execute(text("show application_name"))
        return result.scalar_one()

    assert (await what_the_transaction_is_marked_with()).startswith("boundary-")


async def test_a_context_manager_does_not_hand_the_sync_session_back(bank: BankService):
    """The audit followed dicts and weakrefs and did not follow a frame, so it passed a
    name that hands out the sync Session twice over. no_autoflush is a
    @contextmanager: it yields the Session, and its generator carries the same Session
    in gi_frame.f_locals. run_sync, sync_session, _proxied, object_session and
    _proxy_objects are all refused for handing out that object, and this was a sixth
    name for it that no block list on the session could see."""

    @transactional
    async def what_entering_gives_back() -> bool:
        with current_session().no_autoflush as inside:
            return inside is current_session()

    assert await what_entering_gives_back() is True

    @transactional
    async def reach_through_the_frame() -> None:
        current_session().no_autoflush.gen

    with pytest.raises(TransactionNotYours):
        await reach_through_the_frame()


async def test_a_commit_through_a_context_managers_frame_is_refused(bank: BankService):
    """The route was not theoretical. greenlet_spawn is exactly what run_sync does, so
    the Session reached through the frame committed the boundary's first write, the
    write survived the rollback that was supposed to undo it, and the boundary died on
    a raw InvalidRequestError instead of naming anything."""

    @transactional
    async def half_a_write() -> str:
        await AccountDAO().insert("carol", Decimal("777.00"))
        sync = current_session().no_autoflush.gen.gi_frame.f_locals["self"]
        await greenlet_spawn(sync.commit)
        return "the work is done"

    with pytest.raises(TransactionNotYours):
        await half_a_write()

    assert await bank.list_accounts() == []


async def test_a_deletion_runs_the_same_block_list_as_a_read(bank: BankService):
    """__getattr__ and __setattr__ were guarded and __delattr__ was not, which left the
    third route into an attribute unguarded. It reached nothing on the session, so a
    deletion the caller believed had landed silently had not; and because the names the
    wrapper keeps for itself is one name it hides, deleting it has to be refused by
    name rather than left to land on the session or to recurse. A refusal has to name
    itself, and a RecursionError names nothing."""

    @transactional
    async def delete_a_refused_name() -> None:
        del current_session().commit

    with pytest.raises(TransactionNotYours):
        await delete_a_refused_name()

    @transactional
    async def delete_what_the_wrapper_keeps() -> str:
        with pytest.raises(TransactionNotYours):
            del current_session()._held
        result = await current_session().execute(text("select 1"))
        return f"still alive with {result.scalar_one()}"

    assert await delete_what_the_wrapper_keeps() == "still alive with 1"


async def test_a_split_the_boundary_kept_working_after_is_still_not_a_commit(
    bank: BankService,
):
    """The connection check asked whether a transaction was open, and any session call
    made after the split autobegins a new one, so the answer was yes and the split went
    unnamed. The boundary then failed at COMMIT with a raw InvalidRequestError, which is
    the error the third net exists to replace, and the half committed before the split
    survived. It is the identity of the transaction that has to match, not the fact that
    some transaction is open."""

    @transactional
    async def split_then_carry_on() -> str:
        await AccountDAO().insert("carol", Decimal("777.00"))
        result = await current_session().execute(text("select 1"))
        await AsyncConnection._retrieve_proxy_for_target(result.connection).commit()
        await AccountDAO().insert("dave", Decimal("888.00"))
        return "the work is done"

    with pytest.raises(UnexpectedRollback):
        await split_then_carry_on()

    assert [account.owner for account in await bank.list_accounts()] == ["carol"]


async def test_work_spawned_inside_a_boundary_opens_its_own_transaction_after_it_ends(
    bank: BankService,
):
    """A ContextVar is copied when the task is created, not when it runs, so a
    fire-and-forget task started inside a boundary carried the finished context forever
    and every @transactional call it ever made was refused. The lookup answered "not
    your task" when the truth was "that transaction ended", which is the answer the
    wrapper already gives through the same closed flag. Checking the flag first makes
    the two agree, and a task that outlives the boundary gets a transaction of its
    own instead of a diagnosis that names the wrong thing. It has to really outlive the
    boundary to prove that, so the task waits for an event the caller sets after the
    boundary has returned. Sleeping instead read whatever the scheduler did between
    creating the task and committing: a boundary that does any IO suspends there, and a
    task that wakes up inside one that is still open gets the refusal the test next door
    asks for."""
    account = await bank.open_account("alice", Decimal("10.00"))
    spawned = {}
    the_boundary_has_ended = asyncio.Event()

    @transactional
    async def start_background_work() -> None:
        async def later() -> AccountView:
            await the_boundary_has_ended.wait()
            return await bank.get_account(account.id)

        spawned["task"] = asyncio.create_task(later())

    await start_background_work()
    the_boundary_has_ended.set()

    assert (await spawned["task"]).balance == Decimal("10.00")


async def test_a_task_still_cannot_borrow_a_boundary_that_is_open(bank: BankService):
    """The other half of the change above. Closed first must not mean the task check
    stopped running: while the boundary is open the spawned task is still refused."""

    @transactional
    async def spawn_while_open() -> None:
        await asyncio.create_task(bank.list_accounts())

    with pytest.raises(CrossTaskTransaction):
        await spawn_while_open()


async def test_a_session_call_that_never_reached_the_database_is_not_a_split(
    bank: BankService,
):
    """The connection net compared the transaction it recorded against the one the
    connection holds, and it recorded that identity only after a session call came
    back. A call that raises something the session does not treat as poison - a plain
    string handed to execute() never leaves the process - left the flag saying the
    boundary had reached the database and the identity saying it had not, so the net
    read a live transaction against None and called a boundary that split nothing
    UnexpectedRollback. The flag and the identity are one fact, so the net asks the
    identity."""

    @transactional
    async def swallow_a_failure_that_never_reached_postgres() -> int:
        session = current_session()
        with pytest.raises(Exception) as refused:
            await session.execute("select 1")
        assert not isinstance(refused.value, DBAPIError)
        return (await AccountDAO().insert("alice", Decimal("10.00"))).id

    account_id = await swallow_a_failure_that_never_reached_postgres()

    assert (await bank.get_account(account_id)).owner == "alice"


async def test_a_boundary_whose_only_session_call_failed_still_commits(
    bank: BankService,
):
    """The same hole with nothing after it to hide it. The boundary wrote through no
    session call at all, so there is no result object to reach the connection through
    and nothing that could have split anything; it has to return."""

    @transactional
    async def only_a_failed_call() -> str:
        with pytest.raises(Exception):
            await current_session().execute("select 1")
        return "nothing was written"

    assert await only_a_failed_call() == "nothing was written"


async def test_membership_and_iteration_reach_the_session(bank: BankService):
    """A special method is looked up on the type, not through __getattr__, so the two
    the session defines were not passing through the wrapper at all: `entity in
    session` and `list(session)` were a TypeError naming BoundarySession. That is the
    wrapper silently breaking a session API rather than passing it through or refusing
    it by name, which is the one thing this design is not allowed to do."""

    @transactional
    async def ask_the_session() -> tuple[bool, int]:
        session = current_session()
        account = await AccountDAO().insert("alice", Decimal("10.00"))
        return account in session, len(list(session))

    assert await ask_the_session() == (True, 1)


async def test_every_special_method_the_session_defines_is_on_the_wrapper(
    bank: BankService,
):
    """The block-list audit walks names, and a special method is the one thing a name
    audit cannot see: Python resolves it on the type and never calls __getattr__. So
    the wrapper has to define every one the session does, or the API it exists to pass
    through breaks by accident. This is that audit, and it is what fails when
    SQLAlchemy adds the next one."""
    defined = {
        name
        for name in dir(AsyncSession)
        if name.startswith("__")
        and name not in dir(object)
        and inspect.isfunction(getattr(AsyncSession, name, None))
    }
    missing = {name for name in defined if name not in vars(BoundarySession)}

    assert missing == set(), missing


async def test_a_captured_session_refuses_membership_from_a_spawned_task(
    bank: BankService,
):
    """The special methods run the same guard every other route does, or they are the
    way around it."""
    captured: dict[str, Any] = {}

    @transactional
    async def capture_then_spawn() -> None:
        captured["session"] = current_session()

        async def child() -> None:
            assert object() in captured["session"]

        await asyncio.create_task(child())

    with pytest.raises(CrossTaskTransaction):
        await capture_then_spawn()


async def test_a_boundary_that_only_stages_work_still_commits(bank: BankService):
    """add() stages an entity without an await, so the session wrapper never runs the
    recorder and the boundary reaches its end having never asked the driver anything.
    The connection checks have to stay out of the way there: the only statement is the
    INSERT that session.begin() flushes on the way out, and nothing could have split a
    transaction that had not been opened yet when the method returned."""

    @transactional
    async def stage_only() -> None:
        current_session().add(Account(owner="staged", balance=Decimal("5.00")))

    await stage_only()

    assert [account.owner for account in await bank.list_accounts()] == ["staged"]


async def test_a_session_call_that_sends_no_sql_is_not_a_split(bank: BankService):
    """The driver net latches on the transaction status of the socket, and a flush with
    nothing pending is a session call that comes back without a statement ever leaving
    the process. Postgres is idle, which is not the same as postgres having discarded
    anything, so the net must not fire and the boundary must return."""

    @transactional
    async def flush_nothing() -> str:
        await current_session().flush()
        await current_session().flush()
        return "nothing was pending"

    assert await flush_nothing() == "nothing was pending"


async def test_statements_that_keep_the_transaction_open_are_not_splits(
    bank: BankService,
):
    """The driver net answers a question about the socket, so anything that touches the
    transaction without ending it has to leave it alone. SET LOCAL, a redundant BEGIN
    that Postgres answers with a warning, and a savepoint taken and released by hand all
    keep the connection INTRANS, and a net that fired on any of them would refuse
    boundaries that committed correctly."""

    @transactional
    async def keep_it_open() -> str:
        session = current_session()
        await session.execute(text("set local statement_timeout = 30000"))
        await AccountDAO().insert("alice", Decimal("1.00"))
        await session.execute(text("begin"))
        await session.execute(text("savepoint held"))
        await AccountDAO().insert("bob", Decimal("2.00"))
        await session.execute(text("release savepoint held"))
        return "still one transaction"

    assert await keep_it_open() == "still one transaction"
    assert len(await bank.list_accounts()) == 2


async def test_a_swallowed_argument_error_after_real_work_still_commits(
    bank: BankService,
):
    """The other side of the recorder. A session call that fails without reaching
    Postgres is not poison, so a boundary that swallows one and has already written must
    still commit the write. Refusing here would be the same false alarm as refusing a
    boundary whose only call failed, one successful statement later."""

    @transactional
    async def swallow_after_work() -> str:
        await AccountDAO().insert("alice", Decimal("10.00"))
        with pytest.raises(Exception) as refused:
            await current_session().execute("select 1")
        assert not isinstance(refused.value, DBAPIError)
        return "the write stands"

    assert await swallow_after_work() == "the write stands"
    assert [account.owner for account in await bank.list_accounts()] == ["alice"]


async def test_a_closed_connection_under_the_boundary_is_named(bank: BankService):
    """Closing the Connection a result object carries is the crudest way out of the
    boundary, and the one that leaves SQLAlchemy with nothing coherent to say at COMMIT.
    The connection net catches it as a transaction that ended rather than as whatever
    state error the commit would have produced."""

    @transactional
    async def close_it() -> str:
        await AccountDAO().insert("alice", Decimal("1.00"))
        result = await current_session().execute(text("select 1"))
        await greenlet_spawn(result.connection.close)
        return "the work is done"

    with pytest.raises(UnexpectedRollback) as refused:
        await close_it()

    assert "ended on the connection" in str(refused.value)
    assert await bank.list_accounts() == []


async def test_a_poisoned_boundary_gives_its_connection_back(bank: BankService):
    """A boundary that raises UnexpectedRollback raises it from inside
    session.begin(), which still has to roll back and still has to hand the connection
    to the pool. A leak here is invisible until the pool is empty and every request is a
    503, which is the failure mode the timeouts exist to avoid rather than to cause."""
    await engine.dispose()

    @transactional
    async def poisoned() -> str:
        with pytest.raises(DBAPIError):
            await current_session().execute(text("select 1/0"))
        return "swallowed"

    for _ in range(20):
        with pytest.raises(UnexpectedRollback):
            await poisoned()

    assert engine.pool.checkedout() == 0


async def test_a_cancelled_boundary_gives_its_connection_back(bank: BankService):
    """The same promise for the path that does not raise its way out cleanly. A timeout
    around the boundary cancels it mid-statement, and the connection it was holding has
    to come back rather than stay checked out with a statement still running on it."""
    await engine.dispose()

    @transactional
    async def slow() -> None:
        await current_session().execute(text("select pg_sleep(5)"))

    for _ in range(8):
        with pytest.raises(TimeoutError):
            async with asyncio.timeout(0.05):
                await slow()

    assert engine.pool.checkedout() == 0


async def test_a_refused_task_does_not_poison_the_boundary_that_spawned_it(
    bank: BankService,
):
    """CrossTaskTransaction is raised by the lookup, before the joined-call bookkeeping
    the decorator does, so a caller that spawns a task, is refused and catches the
    refusal has had nothing written on its behalf and nothing to roll back. Poisoning
    there would turn a refusal that protected the transaction into a reason to throw it
    away."""

    @transactional
    async def spawn_and_swallow() -> str:
        await AccountDAO().insert("alice", Decimal("1.00"))
        session = current_session()

        async def child() -> None:
            session.add(Account(owner="ghost", balance=Decimal("0.00")))

        with pytest.raises(CrossTaskTransaction):
            await asyncio.create_task(child())
        return "the caller's own work stands"

    assert await spawn_and_swallow() == "the caller's own work stands"
    assert [account.owner for account in await bank.list_accounts()] == ["alice"]


async def test_the_decorator_applied_twice_is_still_one_transaction(bank: BankService):
    """A wrapper is a coroutine function, so decorating one is legal and the outer call
    joins the inner one by the same rule everything else does. It is a mistake rather
    than a feature, but the propagation rule has to make it harmless instead of opening
    a second transaction nothing would ever commit."""
    sessions = []

    @transactional
    @transactional
    async def twice() -> None:
        sessions.append(current_session())
        await AccountDAO().insert("alice", Decimal("1.00"))

    await twice()

    assert len(sessions) == 1
    assert [account.owner for account in await bank.list_accounts()] == ["alice"]


async def test_transactional_refuses_an_async_generator():
    """An `async def` with a yield in it is an async generator function, not a coroutine
    function, and it is the shape that looks async and is not. Awaiting one gives an
    async_generator object rather than a result, so the boundary would open, commit
    nothing and hand the caller a generator to consume after the session had closed."""
    with pytest.raises(TypeError):

        @transactional
        async def streams():
            yield 1


async def test_a_terminated_backend_is_not_reported_as_a_commit(bank: BankService):
    """The connection can also be taken away rather than misused. Postgres killing the
    backend discards the transaction with nothing on this side raising until the next
    time the boundary touches it, and the boundary has to end as a database error the
    caller can be told about rather than as a commit of work that no longer exists."""

    @transactional
    async def killed_mid_boundary() -> str:
        await AccountDAO().insert("alice", Decimal("1.00"))
        result = await current_session().execute(text("select pg_backend_pid()"))
        backend = result.scalar_one()
        other = result.connection.engine

        def terminate() -> None:
            with other.connect() as connection:
                connection.exec_driver_sql(
                    f"select pg_terminate_backend({backend})"
                )

        await greenlet_spawn(terminate)
        return "the work is done"

    with pytest.raises(OperationalError):
        await killed_mid_boundary()

    assert await bank.list_accounts() == []


async def test_a_savepoint_recovery_by_hand_is_still_a_rollback(bank: BankService):
    """The sharpest consequence of treating every DBAPIError as poison, and an honest
    limit rather than a bug. Postgres can recover an aborted transaction through a
    savepoint, so this boundary really is committable by the time it returns - and the
    boundary refuses it anyway, because the recorder saw the error and nothing tells it
    a savepoint undid the damage. NESTED propagation is what would make this work, and
    it is not implemented; erring the other way would mean reporting success for the
    boundaries that did not recover."""

    @transactional
    async def recover_by_hand() -> str:
        session = current_session()
        await AccountDAO().insert("alice", Decimal("1.00"))
        await session.execute(text("savepoint s"))
        with pytest.raises(DBAPIError):
            await session.execute(text("select 1/0"))
        await session.execute(text("rollback to savepoint s"))
        return "postgres would have committed this"

    with pytest.raises(UnexpectedRollback) as refused:
        await recover_by_hand()

    assert isinstance(refused.value.__cause__, DBAPIError)
    assert await bank.list_accounts() == []


async def test_a_raw_commit_before_any_other_statement_is_caught(bank: BankService):
    """The driver net used to arm itself on the first session call that came back with
    postgres inside a transaction, which made it depend on the order the mistakes are
    made in. A raw COMMIT as the first statement leaves the socket idle, so the net
    never armed, the next call opened a fresh transaction the net then armed on, and
    every check at the end compared that new transaction against itself. The boundary
    marks its transaction on the way in instead, so there is no window before it."""

    @transactional
    async def commit_first() -> str:
        session = current_session()
        await session.execute(text("COMMIT"))
        await AccountDAO().insert("alice", Decimal("1.00"))
        return "success"

    with pytest.raises(UnexpectedRollback):
        await commit_first()

    assert await bank.list_accounts() == []


async def test_a_raw_rollback_before_any_other_statement_is_caught(bank: BankService):
    """The same window in the other direction. A ROLLBACK first discards nothing yet,
    but it proves the net was blind until something armed it, and the work after it
    committed under a boundary that reported success for a transaction it never
    opened."""

    @transactional
    async def rollback_first() -> str:
        session = current_session()
        await session.execute(text("ROLLBACK"))
        await AccountDAO().insert("alice", Decimal("1.00"))
        return "success"

    with pytest.raises(UnexpectedRollback):
        await rollback_first()

    assert await bank.list_accounts() == []


async def test_work_committed_by_a_raw_string_cannot_be_reported_as_success(
    bank: BankService,
):
    """The window with money in it. One statement string that writes and then commits
    hands postgres real work and ends the transaction before any session call could
    arm a net, so the row survived the rollback that followed and the boundary returned
    success over it. The row is still committed - nothing here can undo what postgres
    already kept - but the boundary has to name it rather than call it a commit."""

    @transactional
    async def write_and_commit_in_one_string() -> str:
        await current_session().execute(
            text("INSERT INTO accounts (owner, balance) VALUES ('ghost', 10); COMMIT")
        )
        return "success"

    with pytest.raises(UnexpectedRollback) as refused:
        await write_and_commit_in_one_string()

    assert str(refused.value) in (DISCARDED_BY_POSTGRES, LOST_MARK)


async def test_a_raw_commit_that_opens_another_transaction_is_caught(
    bank: BankService,
):
    """Asking the socket whether a transaction is open cannot tell the boundary's
    transaction from its replacement, and one string can end the first and open the
    second. Every check passed: SQLAlchemy was never told, the connection still held
    the transaction object the boundary recorded, and the driver reported INTRANS
    again. The mark answers the question the status cannot, because postgres throws a
    SET LOCAL away when the transaction it belongs to ends and tells the client it
    did."""

    @transactional
    async def commit_and_open_another() -> str:
        session = current_session()
        await AccountDAO().insert("alice", Decimal("1.00"))
        await session.execute(
            text("COMMIT; BEGIN; INSERT INTO accounts (owner, balance) VALUES ('b', 2)")
        )
        return "success"

    with pytest.raises(UnexpectedRollback) as refused:
        await commit_and_open_another()

    assert str(refused.value) == LOST_MARK


async def test_business_code_that_overwrites_the_mark_is_refused_not_ignored(
    bank: BankService,
):
    """The cost of marking the transaction, paid in the safe direction. Business code
    that sets application_name inside the boundary takes the mark away without ending
    anything, and the boundary refuses a transaction postgres would have committed.
    That is the same side the savepoint case errs on: a named refusal for a boundary
    that was fine beats a silent commit for one that was not."""

    @transactional
    async def take_the_mark() -> str:
        session = current_session()
        await AccountDAO().insert("alice", Decimal("1.00"))
        await session.execute(text("set local application_name = 'mine'"))
        return "success"

    with pytest.raises(UnexpectedRollback) as refused:
        await take_the_mark()

    assert str(refused.value) == LOST_MARK
    assert await bank.list_accounts() == []


async def test_a_boundary_that_cannot_ask_is_not_a_commit(bank: BankService):
    """The five nets answer by asking the session, the connection and the driver, and
    asking is itself a call that can fail. `result.connection.invalidate()` is public
    API off the call every DAO makes, and it leaves SQLAlchemy refusing to hand the
    connection over at all: the boundary died on a raw PendingRollbackError from the
    middle of its own checks, which is a 500 with no diagnosis in it and the one shape
    every other net exists to replace. A boundary that cannot ask whether its
    transaction survived must not report the work as committed, and must say which of
    the two happened. It also has to end like any other refusal: a connection thrown
    away inside the boundary is the one path where a leak would be the boundary's own
    doing, and a leak of one per call is invisible until the pool is empty."""

    @transactional
    async def wreck() -> str:
        await AccountDAO().insert("alice", Decimal("1.00"))
        result = await current_session().execute(text("select 1"))
        result.connection.invalidate()
        return "the work is done"

    for _ in range(40):
        with pytest.raises(UnexpectedRollback) as refused:
            await wreck()
        assert "could not ask" in str(refused.value)
        assert isinstance(refused.value.__cause__, InvalidRequestError)

    assert engine.pool.checkedout() == 0
    assert await bank.list_accounts() == []


async def test_the_wrapper_invents_no_name_of_its_own():
    """A wrapper is not allowed to be a wider door than the thing it wraps, and the
    names it invents are the ones no audit of the session can see: `_session` and
    `_context` were two, `__wrapped__` was a third. The helpers were three more. None
    of them was reachable into anything - `_open` returns the moment the boundary is
    already open - which is exactly how the other three looked before they were not.
    Only `__getattr__` stays, because it is the hook the wrapper is rather than a name
    it hands out."""
    invented = {
        name
        for name in vars(BoundarySession)
        if name not in dir(AsyncSession) and name != "__getattr__"
    }

    assert invented == set(), invented


async def test_no_name_the_wrapper_keeps_shadows_a_name_the_session_has():
    """The wrapper is __getattr__ and __getattr__ only runs for names Python cannot
    find, so every attribute the wrapper defines is a session name it silently swaps
    for its own. The special methods are on it deliberately; a helper is not, and one
    named for a session method would break that API while every test kept passing."""
    helpers = {
        name
        for name in vars(BoundarySession)
        if not (name.startswith("__") and name.endswith("__"))
    }

    assert helpers & set(dir(AsyncSession)) == set()


async def test_an_eager_task_cannot_borrow_the_session(bank: BankService):
    """An eager task factory runs the coroutine synchronously until it first suspends,
    so a create_task() inside a boundary starts on the caller's stack and the refusal
    depends on the eager task making itself current before it does. If it did not, the
    child would drive the session while the lookup still answered for the parent."""
    loop = asyncio.get_running_loop()
    loop.set_task_factory(asyncio.eager_task_factory)

    @transactional
    async def spawn_eagerly() -> None:
        session = current_session()

        async def child() -> None:
            await session.flush()

        await asyncio.create_task(child())

    try:
        with pytest.raises(CrossTaskTransaction):
            await spawn_eagerly()
    finally:
        loop.set_task_factory(None)


async def test_a_thread_running_its_own_loop_cannot_borrow_the_session(
    bank: BankService,
):
    """A worker thread with no loop answers 'no task' and is refused for that. A worker
    thread that starts a loop of its own answers with a real task instead, which is the
    same mistake wearing the shape the check compares against, and the session would be
    driven from two loops at once if the identity were not the thing compared."""

    @transactional
    async def hand_it_to_a_thread() -> None:
        session = current_session()

        def worker() -> None:
            asyncio.run(session.flush())

        await asyncio.to_thread(worker)

    with pytest.raises(CrossTaskTransaction):
        await hand_it_to_a_thread()


async def test_the_schema_refuses_a_balance_that_is_not_a_number(bank: BankService):
    """`balance >= 0` is the backstop for a service bug, and it does not hold the line
    it looks like it holds: postgres orders NaN above every number, so a NaN balance
    satisfies the check. Nothing in the service can write one - every route refuses a
    non-finite amount before the column sees it - but a balance the bank cannot compare
    is worse than a negative one, because reading it back and depositing raises out of
    the decimal module rather than being refused by anything that names it."""
    account = await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def force_a_nan() -> None:
        await current_session().execute(
            text("update accounts set balance = 'NaN' where id = :id"),
            {"id": account.id},
        )

    with pytest.raises(IntegrityError):
        await force_a_nan()

    assert (await bank.get_account(account.id)).balance == Decimal("10.00")


async def test_a_cancellation_racing_the_commit_cannot_split_a_transfer(
    bank: BankService,
):
    """The one window the boundary cannot close, pinned for what it can promise inside
    it. A cancellation that lands after the method returned races the COMMIT already on
    its way to postgres, and the server decides the outcome: some of these transfers
    commit while their caller is told the call was cancelled. What must never happen is
    a transfer that is half of one - money moved with no ledger row, or a debit with no
    credit - or the other direction, a boundary that returned and did not commit. Every
    transfer here is 1.00, so the ledger row count is the money that moved."""
    source = (await bank.open_account("alice", Decimal("100.00"))).id
    target = (await bank.open_account("bob", Decimal("0.00"))).id
    returned = 0

    for attempt in range(60):
        call = asyncio.create_task(bank.transfer(source, target, Decimal("1.00")))
        await asyncio.sleep(attempt / 60 * 0.020)
        call.cancel()
        try:
            await call
            returned += 1
        except asyncio.CancelledError:
            pass

    accounts = {account.owner: account.balance for account in await bank.list_accounts()}
    committed = len(await bank.list_ledger())

    assert accounts["bob"] == Decimal(committed)
    assert accounts["alice"] + accounts["bob"] == Decimal("100.00")
    assert returned <= committed


async def test_the_sessionmakers_own_context_manager_is_refused(bank: BankService):
    """_maker_context_manager is what async_sessionmaker.begin() runs, and it is a name
    on the session like any other. What it hands back holds the raw AsyncSession, opens
    a transaction on entry and closes the session on exit, so it is begin and close
    under a name the list did not have. It was already impossible, but only by accident
    - SQLAlchemy answers a second begin() with a raw InvalidRequestError - and a
    refusal by accident is not an answer the caller can act on, which is the same
    argument that put the session's own async with on the list."""

    @transactional
    async def through_the_maker() -> str:
        session = current_session()
        await AccountDAO().insert("alice", Decimal("1.00"))
        async with session._maker_context_manager():
            pass
        return "success"

    with pytest.raises(TransactionNotYours) as refused:
        await through_the_maker()

    assert "_maker_context_manager" in str(refused.value)
    assert await bank.list_accounts() == []


async def test_no_call_on_the_wrapper_hands_back_the_engine_or_the_sync_session(
    bank: BankService,
):
    """The audit next door walks what every name is and could not see what a name does.
    _maker_context_manager is a routine, so the sweep read a function object and moved
    on, while calling it handed back an object holding the AsyncSession itself. This
    calls every name that needs no arguments and looks inside what comes back, through
    its __dict__ and its __slots__, so the next name of that shape is a failing test
    rather than a paragraph."""

    def takes_no_arguments(value: Any) -> bool:
        try:
            parameters = inspect.signature(value).parameters.values()
        except (TypeError, ValueError):
            return False
        return all(
            parameter.default is not inspect.Parameter.empty
            or parameter.kind
            in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            for parameter in parameters
        )

    def held(value: Any) -> list[Any]:
        names = list(getattr(type(value), "__slots__", ()))
        names += list(getattr(value, "__dict__", {}))
        found = []
        for name in names:
            try:
                found.append(getattr(value, name))
            except BaseException:
                pass
        return found

    @transactional
    async def sweep() -> list[str]:
        wrapper = current_session()
        escapes = (
            Engine,
            AsyncEngine,
            Session,
            AsyncSession,
            Connection,
            AsyncConnection,
            Transaction,
            SessionTransaction,
        )
        leaked = []
        for name in dir(wrapper):
            if name.startswith("__"):
                continue
            try:
                value = getattr(wrapper, name)
            except (TransactionNotYours, AttributeError):
                continue
            if not (inspect.isroutine(value) and takes_no_arguments(value)):
                continue
            try:
                answer = value()
                if inspect.isawaitable(answer):
                    answer = await answer
            except BaseException:
                continue
            if any(isinstance(one, escapes) for one in [answer] + held(answer)):
                leaked.append(name)
        return leaked

    assert await sweep() == []


async def test_a_mark_put_back_by_hand_is_the_limit_the_mark_leaves_open(
    bank: BankService,
):
    """The mark answers whether postgres is still in the transaction the boundary
    opened, and it answers it by reading a value the transaction carries. SHOW hands
    that value to the code inside the boundary, so code that ends the transaction and
    sets the same application_name on the one it opens in its place puts every net back
    the way it found them: SQLAlchemy was never told, the connection holds the
    transaction object the boundary recorded, the driver reports INTRANS, and the mark
    reads back as the boundary's own. The row the raw COMMIT wrote survives and the
    boundary calls it a success. It is the same kind of limit _session is: a guard
    against a mistake cannot survive code that is aiming at it, and a suite that only
    showed what is caught would leave the reader thinking otherwise."""

    @transactional
    async def forge_the_mark() -> str:
        session = current_session()
        await AccountDAO().insert("alice", Decimal("1.00"))
        mark = (await session.execute(text("show application_name"))).scalar_one()
        await session.execute(
            text(f"commit; begin; set local application_name = '{mark}'")
        )
        return "success"

    assert await forge_the_mark() == "success"
    assert [account.owner for account in await bank.list_accounts()] == ["alice"]


async def test_a_cancellation_after_a_swallowed_failure_is_still_a_cancellation(
    bank: BankService,
):
    """A boundary that a joined failure had already poisoned, and that is then
    cancelled, used to answer with UnexpectedRollback. That swallows the cancellation,
    which asyncio does not allow: the task did not end cancelled, so a caller awaiting
    it was told the work had failed rather than been stopped, and the CancelledError
    that asyncio was waiting to see never arrived. Converting it bought nothing either,
    because an exception leaving the boundary rolls the transaction back whichever one
    it is. So a BaseException that is not an Exception propagates as itself and the
    poison it would have named is its __cause__ instead."""
    account = await bank.open_account("alice", Decimal("100.00"))

    @transactional
    async def boundary() -> None:
        try:
            await bank.withdraw(account.id, Decimal("999.00"))
        except InsufficientFunds:
            pass
        await asyncio.sleep(3600)

    task = asyncio.ensure_future(boundary())
    await asyncio.sleep(0.1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError) as raised:
        await task

    assert task.cancelled()
    assert isinstance(raised.value.__cause__, InsufficientFunds)
    assert (await bank.get_account(account.id)).balance == Decimal("100.00")


async def test_a_timeout_around_a_poisoned_boundary_is_still_a_timeout(
    bank: BankService,
):
    """The same swallowed cancellation seen from the shape it actually takes.
    asyncio.timeout only turns a cancellation into TimeoutError if the CancelledError
    reaches it, so a boundary that answered with UnexpectedRollback instead left the
    caller's timeout looking like a transaction bug. The rollback is the same either
    way; what changes is whether the caller can tell why it was stopped."""
    account = await bank.open_account("bob", Decimal("100.00"))

    @transactional
    async def boundary() -> None:
        try:
            await bank.withdraw(account.id, Decimal("999.00"))
        except InsufficientFunds:
            pass
        await asyncio.sleep(3600)

    with pytest.raises(TimeoutError):
        async with asyncio.timeout(0.1):
            await boundary()

    assert (await bank.get_account(account.id)).balance == Decimal("100.00")


async def test_a_swallowed_failure_still_names_itself_when_the_caller_trips_again(
    bank: BankService,
):
    """The half of that rule which has to keep working: an ordinary exception after a
    swallowed failure is still replaced by UnexpectedRollback naming the poison, and
    only a BaseException that asyncio owns is let through as itself."""
    account = await bank.open_account("carol", Decimal("100.00"))

    @transactional
    async def boundary() -> None:
        try:
            await bank.withdraw(account.id, Decimal("999.00"))
        except InsufficientFunds:
            pass
        raise ValueError("something else went wrong")

    with pytest.raises(UnexpectedRollback) as raised:
        await boundary()

    assert isinstance(raised.value.__cause__, InsufficientFunds)
    assert isinstance(raised.value.__context__, ValueError)


async def test_transactional_refuses_a_callable_that_is_not_a_function(
    bank: BankService,
):
    """The decorator promises a TypeError at import rather than a confusing error
    later, and an object with an async __call__ is the shape that broke the promise:
    it is not a coroutine function, so the refusal fired, but the message reached for
    __name__ on something that has none and the caller got an AttributeError about
    __ne__ instead of being told what @transactional needs."""

    class Service:
        async def __call__(self) -> None:
            pass

    with pytest.raises(TypeError) as raised:
        transactional(Service())

    assert "async def" in str(raised.value)
    assert "Service" in str(raised.value)


async def test_a_swallowed_cancellation_leaves_the_task_cancelled(bank: BankService):
    """The mirror of the rule that a cancellation leaving a poisoned boundary stays a
    cancellation, and it was open. Here the cancellation is the poison and the business
    code swallows it - a retry loop around `except BaseException` is the shape it takes -
    so nothing propagates and the boundary reached the rollback-only check on a normal
    return. Answering UnexpectedRollback there swallowed the cancellation the caller was
    still under: the task did not end cancelled and whoever asked for it to stop was told
    the work had failed instead. Rolling back is not in question either way; what changes
    is whether the task ends the way asyncio was promised it would."""
    account = await bank.open_account("alice", Decimal("100.00"))

    @transactional
    async def boundary() -> str:
        await bank.deposit(account.id, Decimal("50.00"))
        for _ in range(3):
            try:
                await current_session().execute(text("select pg_sleep(5)"))
                break
            except BaseException:
                continue
        return "the retries are done"

    task = asyncio.ensure_future(boundary())
    await asyncio.sleep(0.2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert task.cancelled()
    assert (await bank.get_account(account.id)).balance == Decimal("100.00")


async def test_a_timeout_around_a_boundary_that_swallowed_it_is_still_a_timeout(
    bank: BankService,
):
    """The same hole from the shape a caller actually writes. asyncio.timeout only
    becomes a TimeoutError when the CancelledError it sent reaches it, so a boundary that
    answered UnexpectedRollback instead left a caller's own deadline looking like a
    transaction bug. The timeout is outside the boundary here, which is what makes the
    cancellation still outstanding when the boundary finishes; a timeout the business
    code puts inside itself has already turned its cancellation into a TimeoutError and
    uncancelled the task, and that one still answers UnexpectedRollback."""
    account = await bank.open_account("bob", Decimal("100.00"))

    @transactional
    async def boundary() -> str:
        await bank.deposit(account.id, Decimal("50.00"))
        try:
            await current_session().execute(text("select pg_sleep(5)"))
        except BaseException:
            pass
        return "swallowed it"

    with pytest.raises(TimeoutError):
        async with asyncio.timeout(0.2):
            await boundary()

    assert (await bank.get_account(account.id)).balance == Decimal("100.00")


async def test_a_taskgroup_is_told_its_boundary_was_stopped_not_that_it_failed(
    bank: BankService,
):
    """The consequence of the same rule one layer up, and the reason it is worth a
    net of its own. A TaskGroup cancels its remaining children when one of them fails,
    and a child that ends with anything other than CancelledError is collected into the
    group as a second failure. So a boundary that swallowed its cancellation turned one
    error into two and named a transaction problem that never happened."""
    account = await bank.open_account("carol", Decimal("100.00"))

    @transactional
    async def boundary() -> None:
        await bank.deposit(account.id, Decimal("50.00"))
        try:
            await current_session().execute(text("select pg_sleep(5)"))
        except BaseException:
            pass

    async def fails() -> None:
        await asyncio.sleep(0.2)
        raise InvalidOwner("the sibling is the one that failed")

    with pytest.raises(BaseExceptionGroup) as raised:
        async with asyncio.TaskGroup() as group:
            group.create_task(boundary())
            group.create_task(fails())

    assert [type(error) for error in raised.value.exceptions] == [InvalidOwner]
    assert (await bank.get_account(account.id)).balance == Decimal("100.00")


async def test_a_commit_and_chain_is_caught_by_the_mark_alone(bank: BankService):
    """The shape every net but the last one passes. `COMMIT AND CHAIN` ends the
    transaction and opens another with the same characteristics in the same statement,
    so SQLAlchemy is never told, the Connection still holds the transaction object the
    boundary recorded, and the driver reports INTRANS because a transaction really is
    open - it is simply not the one the boundary started. Only the mark can tell those
    apart, and the money is real: the row committed by the chain survives the rollback,
    which is exactly why the boundary must not call the result a success."""
    account = await bank.open_account("alice", Decimal("100.00"))

    @transactional
    async def boundary() -> str:
        session = current_session()
        await bank.deposit(account.id, Decimal("30.00"))
        await session.execute(text("commit and chain"))
        return "the boundary returned"

    with pytest.raises(UnexpectedRollback) as raised:
        await boundary()

    assert str(raised.value) == LOST_MARK
    assert (await bank.get_account(account.id)).balance == Decimal("130.00")


async def test_the_words_for_commit_and_rollback_are_not_what_is_watched(
    bank: BankService,
):
    """`END` and `ABORT` are postgres' own aliases, so a net that matched on the SQL
    would have missed both. Nothing here reads the statement: END leaves the socket idle
    and the driver says so, ABORT leaves a fresh transaction the mark cannot be in, and
    the two arrive as different refusals for that reason."""

    @transactional
    async def ends() -> None:
        await current_session().execute(text("end"))

    @transactional
    async def aborts() -> None:
        session = current_session()
        await session.execute(text("abort"))
        await session.execute(text("select 1"))

    with pytest.raises(UnexpectedRollback) as ended:
        await ends()
    with pytest.raises(UnexpectedRollback) as aborted:
        await aborts()

    assert str(ended.value) == DISCARDED_BY_POSTGRES
    assert str(aborted.value) == LOST_MARK
    assert await bank.list_accounts() == []


async def test_autocommit_has_no_way_into_the_boundary(bank: BankService):
    """Autocommit is the one setting that would end the transaction under every net at
    once, because there would be no transaction left for any of them to ask about. It
    has two entrances and both are shut before the database hears anything: SQLAlchemy
    refuses isolation_level as a statement option with an ArgumentError, and the
    connection-level option it points the caller at needs connection(), which is the
    boundary's. Nothing reached postgres either way, so the work around it still
    commits, which is the half a refusal is only worth having if it keeps."""
    account = await bank.open_account("alice", Decimal("100.00"))

    @transactional
    async def boundary() -> str:
        session = current_session()
        await bank.deposit(account.id, Decimal("30.00"))
        with pytest.raises(ArgumentError):
            await session.execute(
                text("select 1").execution_options(isolation_level="AUTOCOMMIT")
            )
        with pytest.raises(TransactionNotYours):
            await session.connection(
                execution_options={"isolation_level": "AUTOCOMMIT"}
            )
        return "the boundary returned"

    assert await boundary() == "the boundary returned"
    assert (await bank.get_account(account.id)).balance == Decimal("130.00")


async def test_the_sync_session_an_entity_carries_cannot_commit(bank: BankService):
    """object_session() is refused as a name on the wrapper, but the same function
    imported from SQLAlchemy answers for any entity a DAO loaded, and that is an object
    the boundary never handed out and cannot take back. The Session it hands back cannot
    be driven from async code at all, so the commit fails where it is written instead of
    splitting the transaction quietly - but it fails half way through, leaving postgres
    inside a transaction that SQLAlchemy has already stopped tracking. Nothing rolled
    that back, the connection went into the pool still holding it, and the next boundary
    to check it out died on a pre-ping that cannot run in a transaction: a mistake in one
    request answered as a 500 in an unrelated one. The boundary asks the driver before it
    lets go, so what it gives back is a connection with no transaction on it."""
    from sqlalchemy.orm import object_session

    @transactional
    async def boundary() -> None:
        account = await AccountDAO().insert("alice", Decimal("100.00"))
        object_session(account).commit()

    with pytest.raises(InvalidRequestError):
        await boundary()

    assert await bank.list_accounts() == []
    assert (await bank.open_account("bob", Decimal("1.00"))).owner == "bob"


async def test_every_refused_boundary_gives_its_connection_back(bank: BankService):
    """A boundary the nets refuse still has to end like any other one. The rollback runs
    against a transaction postgres has already thrown away, which is the path that leaks
    a connection if the session is not closed underneath it, and a leak of one per call
    is invisible until the pool is empty and every request is a 503. Forty of them in a
    row is more than the pool plus its overflow can hold."""

    @transactional
    async def split() -> None:
        await current_session().execute(text("commit"))

    for _ in range(40):
        with pytest.raises(UnexpectedRollback):
            await split()

    assert engine.pool.checkedout() == 0
    assert await bank.list_accounts() == []


async def test_the_service_hands_out_views_and_never_an_entity(bank: BankService):
    """The boundary closes the session that loaded every entity it touched, so an
    `Account` that reaches the controller is a detached object whose next attribute read
    is a `DetachedInstanceError` - a 500 in the layer furthest from the mistake. Nothing
    in the decorator can stop a service from returning one, so the guarantee is a shape
    the service keeps and this is the test that keeps it: every call is made, and every
    value that comes back is read after its boundary has ended."""
    ledger = LedgerService()
    alice = await bank.open_account("alice", Decimal("100.00"))
    bob = await bank.open_account("bob", Decimal("0.00"))
    answers = [
        alice,
        bob,
        await bank.get_account(alice.id),
        await bank.deposit(alice.id, Decimal("1.00")),
        await bank.withdraw(alice.id, Decimal("1.00")),
        await bank.transfer(alice.id, bob.id, Decimal("10.00")),
        await ledger.record(alice.id, bob.id, Decimal("1.00")),
        *await bank.list_accounts(),
        *await bank.list_ledger(),
        *await ledger.list_all(),
    ]

    for answer in answers:
        assert not isinstance(answer, Account), answer
        assert [str(getattr(answer, field)) for field in vars(answer)]


async def test_a_two_phase_prepare_cannot_end_the_boundarys_transaction(
    bank: BankService,
):
    """`PREPARE TRANSACTION` is the one statement that ends a transaction without
    committing or rolling it back: the work stays durable and locked under a name the
    boundary never learns, so a boundary that returned would be holding rows nothing
    releases. Postgres ships with `max_prepared_transactions = 0`, which is what refuses
    it here, and the point of the test is that the refusal is answered as poison rather
    than left to a caller who swallowed it."""

    @transactional
    async def prepare() -> str:
        await AccountDAO().insert("alice", Decimal("1.00"))
        try:
            await current_session().execute(text("prepare transaction 'boundary'"))
        except OperationalError:
            pass
        return "the work is done"

    with pytest.raises(UnexpectedRollback):
        await prepare()

    assert await bank.list_accounts() == []


async def test_a_boundary_cancelled_waiting_for_a_lock_releases_nothing_and_holds_nothing(
    bank: BankService,
):
    """The sibling of the mid-statement cancellation, and the one with teeth. A boundary
    blocked on `FOR UPDATE` is parked inside Postgres, not sleeping in Python, so the
    cancellation has to reach the server before the connection can go back. If it does
    not, the row stays locked by a transaction nobody is waiting on any more and the
    account is wedged for every later request - a hot row that never unblocks, which is
    the failure this whole locking scheme exists to avoid."""
    alice = await bank.open_account("alice", Decimal("100.00"))
    holding, finished = asyncio.Event(), asyncio.Event()

    @transactional
    async def hold() -> None:
        await bank.lock_account(alice.id)
        holding.set()
        await finished.wait()

    holder = asyncio.create_task(hold())
    await holding.wait()
    waiters = [
        asyncio.create_task(bank.deposit(alice.id, Decimal("1.00"))) for _ in range(5)
    ]
    await asyncio.sleep(0.2)
    for waiter in waiters:
        waiter.cancel()
    outcomes = await asyncio.gather(*waiters, return_exceptions=True)
    finished.set()
    await holder

    assert all(isinstance(outcome, asyncio.CancelledError) for outcome in outcomes)
    assert (await bank.get_account(alice.id)).balance == Decimal("100.00")
    assert (await bank.deposit(alice.id, Decimal("1.00"))).balance == Decimal("101.00")
    assert engine.pool.checkedout() == 0


ESCAPES = (
    Engine,
    AsyncEngine,
    Session,
    AsyncSession,
    Connection,
    AsyncConnection,
    Transaction,
    SessionTransaction,
)


def reachable(value: Any) -> list[Any]:
    found = [value]
    for name in ("__self__", "__func__", "__wrapped__"):
        try:
            found.append(getattr(value, name))
        except BaseException:
            pass
    try:
        found += [cell.cell_contents for cell in (value.__closure__ or ())]
    except BaseException:
        pass
    try:
        found += list(value.__dict__.values())
    except BaseException:
        pass
    return [held for one in found for held in inside(one)]


def inside(value: Any, depth: int = 3) -> list[Any]:
    if depth == 0:
        return [value]
    if isinstance(value, dict):
        held = [*value.keys(), *value.values()]
    elif isinstance(value, (list, tuple, set, frozenset)):
        held = list(value)
    elif isinstance(value, ReferenceType):
        held = [value()]
    else:
        return [value]
    return [value, *(one for held_one in held for one in inside(held_one, depth - 1))]


def escaped(value: Any) -> list[str]:
    return [type(one).__name__ for one in reachable(value) if isinstance(one, ESCAPES)]


async def test_a_call_the_wrapper_hands_out_is_not_a_handle_on_the_one_it_wraps(
    bank: BankService,
):
    """functools.wraps sets __wrapped__ on everything it decorates, so every call the
    wrapper handed out carried the raw bound method of the AsyncSession under a
    documented name. Reaching it skipped the guard entirely, which meant _open() never
    ran: no connection was marked, no driver and no transaction identity were recorded,
    and three of the five nets were switched off for the rest of the boundary. An INSERT
    and a raw COMMIT sent through it wrote a row that survived, and the boundary
    returned success. The wrapper keeps the name and the docstring of the call it stands
    in for and hands back no route to it."""

    @transactional
    async def the_old_way_in() -> str:
        raw = current_session().execute.__wrapped__
        await raw(text("insert into accounts (owner, balance) values ('alice', 1.00)"))
        await raw(text("commit"))
        return "the work is done"

    with pytest.raises(AttributeError):
        await the_old_way_in()

    assert await bank.list_accounts() == []

    @transactional
    async def what_a_call_carries() -> tuple[str, str, list[str], list[str]]:
        session = current_session()
        return (
            session.execute.__name__,
            session.add.__name__,
            escaped(session.execute),
            escaped(session.add),
        )

    assert await what_a_call_carries() == ("execute", "add", [], [])


async def test_the_wrapper_hides_the_one_name_it_keeps_for_itself(bank: BankService):
    """The wrapper has to hold the session and the transaction somewhere, and it held
    them in its own __dict__ under _session and _context. Both were plain instance
    attributes: reading one handed back the AsyncSession, and writing to _context turned
    the nets off from inside the boundary - driver = None skipped the last three checks
    and the rollback that gives the connection back clean, closed = True made the next
    joined call open a second transaction that committed on its own while the outer one
    rolled back. A wrapper is not allowed to be a wider door than the thing it wraps, and
    the session it stands in for has no such name."""

    @transactional
    async def reach_for_what_the_wrapper_keeps() -> list[str]:
        session = current_session()
        refused = []
        for name in ("_held", "__dict__"):
            try:
                getattr(session, name)
            except TransactionNotYours:
                refused.append(f"get {name}")
            try:
                setattr(session, name, None)
            except TransactionNotYours:
                refused.append(f"set {name}")
            try:
                delattr(session, name)
            except TransactionNotYours:
                refused.append(f"del {name}")
        try:
            vars(session)
        except TransactionNotYours:
            refused.append("vars")
        return refused

    assert await reach_for_what_the_wrapper_keeps() == [
        "get _held",
        "set _held",
        "del _held",
        "get __dict__",
        "set __dict__",
        "del __dict__",
        "vars",
    ]

    @transactional
    async def the_old_names_are_the_sessions_answer() -> list[str]:
        session = current_session()
        missing = []
        for name in ("_session", "_context"):
            try:
                getattr(session, name)
            except AttributeError as error:
                missing.append(type(error).__name__ + " " + name)
        return missing

    assert await the_old_names_are_the_sessions_answer() == [
        "AttributeError _session",
        "AttributeError _context",
    ]


async def test_the_pickle_protocol_does_not_hand_the_session_out(bank: BankService):
    """Hiding a name from getattr is not hiding it: object.__reduce_ex__ reads the
    instance __dict__ in C, under the attribute hook rather than through it, and handed
    the whole state back as the second half of a reduce tuple - the AsyncSession and the
    TransactionContext both, to anything that pickled or copied the session. copy.copy()
    was worse than a leak before that: rebuilding the wrapper without its state left
    __getattr__ asking for a name that was not there and recursing until Python gave up,
    so the answer to an ordinary copy was a RecursionError naming nothing."""

    @transactional
    async def every_way_at_the_state() -> list[tuple[str, str]]:
        session = current_session()
        attempts = {
            "__getstate__": lambda: session.__getstate__(),
            "__reduce__": lambda: session.__reduce__(),
            "__reduce_ex__": lambda: session.__reduce_ex__(2),
            "pickle": lambda: pickle.dumps(session),
            "copy": lambda: copy.copy(session),
            "deepcopy": lambda: copy.deepcopy(session),
        }
        answers = []
        for name, attempt in attempts.items():
            try:
                answers.append((name, f"handed back {escaped(attempt())}"))
            except TransactionNotYours:
                answers.append((name, "refused"))
            except BaseException as error:
                answers.append((name, type(error).__name__))
        return answers

    assert await every_way_at_the_state() == [
        ("__getstate__", "refused"),
        ("__reduce__", "refused"),
        ("__reduce_ex__", "refused"),
        ("pickle", "refused"),
        ("copy", "refused"),
        ("deepcopy", "refused"),
    ]


async def test_no_dunder_on_the_wrapper_hands_back_the_engine_or_the_sync_session(
    bank: BankService,
):
    """The two sweeps next door walk dir() and skip every name that starts with two
    underscores, which is exactly where the last escapes were: __dict__ held the session
    and __reduce_ex__ handed the same dict out through the copy protocol. A dunder is
    still a name, and Python calls more of them on an object than any caller ever types
    by hand."""

    @transactional
    async def sweep() -> list[str]:
        wrapper = current_session()
        leaked = []
        for name in sorted(set(dir(wrapper)) | set(dir(object)) | set(dir(type))):
            if not name.startswith("__"):
                continue
            try:
                value = getattr(wrapper, name)
            except BaseException:
                continue
            if escaped(value):
                leaked.append(name)
        return leaked

    assert await sweep() == []


async def test_the_holder_for_a_context_manager_hides_what_it_holds(bank: BankService):
    """no_autoflush is wrapped rather than refused, because entering it is a legitimate
    thing for a DAO to do. The holder that wraps it kept the manager and the wrapper in
    its own __dict__ the same way, so vars() on it handed back the generator whose frame
    carries the sync Session - the sixth name for the object the other five are refused
    for, reached without typing any of them."""

    @transactional
    async def reach_into_the_holder() -> list[str]:
        holder = current_session().no_autoflush
        refused = []
        for attempt in (
            lambda: getattr(holder, "_held"),
            lambda: vars(holder),
            lambda: holder.__reduce_ex__(2),
            lambda: getattr(holder, "gen"),
        ):
            try:
                attempt()
            except TransactionNotYours:
                refused.append("refused")
        return refused

    assert await reach_into_the_holder() == ["refused"] * 4

    @transactional
    async def entering_it_still_works() -> str:
        with current_session().no_autoflush as inside:
            account = await AccountDAO().insert("alice", Decimal("1.00"))
        return f"{type(inside).__name__} kept {account.owner}"

    assert await entering_it_still_works() == "BoundarySession kept alice"
    assert [account.owner for account in await bank.list_accounts()] == ["alice"]


async def test_the_wrapper_answers_dir_the_way_the_session_does(bank: BankService):
    """Hiding __dict__ breaks the default __dir__, which reads it, and a wrapper that
    cannot be listed is a wrapper that has broken a session API to protect itself. It
    answers with the session's own names instead, which is what a caller asking a
    session what it can do is asking for - and what the two sweeps walk, so an escape
    added to the session is an escape they now see."""

    @transactional
    async def what_it_lists() -> tuple[bool, bool, bool]:
        session = current_session()
        names = dir(session)
        return "execute" in names, "sync_session" in names, "_held" in names

    assert await what_it_lists() == (True, True, False)


async def test_a_commit_through_the_session_an_entity_carries_is_not_a_commit(
    bank: BankService,
):
    """object_session and _proxied are refused on the wrapper, and SQLAlchemy hands the
    same AsyncSession back from module level: async_object_session() takes any entity the
    session has and returns the session itself. No private name is typed and nothing is
    imported that a DAO does not already import. It reached an unwatched boundary
    because the mark went on at the first async call, and the entity here is staged with
    session.add(), which is sync: a raw COMMIT then ran on a transaction with no driver,
    no identity and no mark recorded against it, and the boundary returned success over
    two rows it had not committed. The mark goes on before any of this code runs, so the
    same COMMIT is the mark going missing."""

    @transactional
    async def commit_it_by_hand() -> str:
        session = current_session()
        staged = Account(owner="carol", balance=Decimal("1.00"))
        session.add(staged)
        raw = async_object_session(staged)
        assert isinstance(raw, AsyncSession)
        await raw.execute(text("commit"))
        await raw.execute(
            text("insert into accounts (owner, balance) values ('dave', 2.00)")
        )
        return "the work is done"

    with pytest.raises(UnexpectedRollback) as refused:
        await commit_it_by_hand()

    assert str(refused.value) == LOST_MARK
    assert await bank.list_accounts() == []
