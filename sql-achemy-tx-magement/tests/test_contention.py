import asyncio
from decimal import Decimal

import pytest
from sqlalchemy import text

from dao import AccountDAO, LedgerDAO
from service import BankService, InsufficientFunds, LedgerService
from tx import current_session, transactional


@transactional
async def ledger_sequence() -> int:
    result = await current_session().execute(
        text("select last_value from ledger_id_seq")
    )
    return result.scalar_one()


async def total_balance(bank: BankService) -> Decimal:
    return sum((a.balance for a in await bank.list_accounts()), Decimal("0.00"))


async def test_concurrent_withdrawals_cannot_overdraw_the_account(bank: BankService):
    account = await bank.open_account("alice", Decimal("100.00"))

    results = await asyncio.gather(
        *(bank.withdraw(account.id, Decimal("100.00")) for _ in range(10)),
        return_exceptions=True,
    )

    winners = [r for r in results if not isinstance(r, BaseException)]
    losers = [r for r in results if isinstance(r, InsufficientFunds)]
    assert len(winners) == 1
    assert len(losers) == 9
    assert (await bank.get_account(account.id)).balance == Decimal("0.00")


async def test_concurrent_deposits_do_not_lose_updates(bank: BankService):
    account = await bank.open_account("alice", Decimal("0.00"))

    await asyncio.gather(*(bank.deposit(account.id, Decimal("10.00")) for _ in range(10)))

    assert (await bank.get_account(account.id)).balance == Decimal("100.00")


async def test_transfers_in_opposite_directions_do_not_deadlock(bank: BankService):
    alice = await bank.open_account("alice", Decimal("100.00"))
    bob = await bank.open_account("bob", Decimal("100.00"))

    results = await asyncio.gather(
        *(
            bank.transfer(alice.id, bob.id, Decimal("10.00"))
            if index % 2 == 0
            else bank.transfer(bob.id, alice.id, Decimal("10.00"))
            for index in range(10)
        ),
        return_exceptions=True,
    )

    assert [r for r in results if isinstance(r, BaseException)] == []
    assert await total_balance(bank) == Decimal("200.00")


async def test_money_is_conserved_under_concurrent_transfers(bank: BankService):
    owners = ["alice", "bob", "carol", "dave"]
    accounts = [await bank.open_account(owner, Decimal("50.00")) for owner in owners]
    before = await total_balance(bank)

    pairs = [(accounts[i % 4], accounts[(i + 1) % 4]) for i in range(12)]
    results = await asyncio.gather(
        *(bank.transfer(s.id, t.id, Decimal("20.00")) for s, t in pairs),
        return_exceptions=True,
    )

    committed = [r for r in results if not isinstance(r, BaseException)]
    refused = [r for r in results if isinstance(r, BaseException)]
    assert committed
    assert all(isinstance(r, InsufficientFunds) for r in refused)
    assert len(await bank.list_ledger()) == len(committed)
    assert await total_balance(bank) == before
    assert all(a.balance >= 0 for a in await bank.list_accounts())


async def test_propagation_holds_under_concurrency(
    bank: BankService, monkeypatch: pytest.MonkeyPatch
):
    per_task: dict[object, list] = {}
    original_insert = LedgerDAO.insert
    original_update = AccountDAO.update_balance

    def record() -> None:
        per_task.setdefault(asyncio.current_task(), []).append(current_session())

    async def spy_insert(self, source_id, target_id, amount):
        record()
        return await original_insert(self, source_id, target_id, amount)

    async def spy_update(self, account, balance):
        record()
        return await original_update(self, account, balance)

    monkeypatch.setattr(LedgerDAO, "insert", spy_insert)
    monkeypatch.setattr(AccountDAO, "update_balance", spy_update)
    accounts = [
        await bank.open_account(owner, Decimal("100.00"))
        for owner in ["alice", "bob", "carol", "dave"]
    ]

    await asyncio.gather(
        *(
            bank.transfer(accounts[i].id, accounts[(i + 1) % 4].id, Decimal("5.00"))
            for i in range(4)
        )
    )

    assert len(per_task) == 4
    for sessions in per_task.values():
        assert len(sessions) == 3
        assert sessions[0] is sessions[1] is sessions[2]
    first_of_each = [sessions[0] for sessions in per_task.values()]
    assert len({id(session) for session in first_of_each}) == 4


async def test_a_rolled_back_insert_really_reached_the_database(bank: BankService):
    alice = await bank.open_account("alice", Decimal("100.00"))
    bob = await bank.open_account("bob", Decimal("0.00"))
    await bank.transfer(alice.id, bob.id, Decimal("10.00"))
    committed = await ledger_sequence()

    with pytest.raises(InsufficientFunds):
        await bank.transfer(alice.id, bob.id, Decimal("9999.00"))

    assert await ledger_sequence() == committed + 1
    assert len(await bank.list_ledger()) == 1


async def test_recording_a_ledger_entry_does_not_deadlock_with_a_transfer(
    bank: BankService,
):
    """Inserting a ledger row takes a foreign key lock on each account it names, in the
    order the columns are declared, not in ascending id order. Against a transfer that
    locks ascending that is the classic ABBA deadlock, so record() has to take the same
    ascending lock a transfer takes before it inserts."""
    alice = await bank.open_account("alice", Decimal("1000.00"))
    bob = await bank.open_account("bob", Decimal("1000.00"))
    high, low = max(alice.id, bob.id), min(alice.id, bob.id)
    ledger = LedgerService()

    results = await asyncio.gather(
        *(
            ledger.record(high, low, Decimal("1.00"))
            if index % 2
            else bank.transfer(low, high, Decimal("1.00"))
            for index in range(20)
        ),
        return_exceptions=True,
    )

    assert [r for r in results if isinstance(r, BaseException)] == []
    assert await total_balance(bank) == Decimal("2000.00")
