import asyncio
import inspect
import re
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import controller
import tx
from controller import app
from db import DATABASE_URL, TIMEOUTS
from service import BankService, InsufficientFunds
from tx import transactional


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://bank") as client:
        yield client


async def test_transfer_endpoint_moves_money_and_records_the_ledger(
    client: httpx.AsyncClient,
):
    source = await client.post(
        "/api/accounts", json={"owner": "alice", "initial_balance": "100.00"}
    )
    target = await client.post(
        "/api/accounts", json={"owner": "bob", "initial_balance": "0.00"}
    )
    source_id = source.json()["id"]
    target_id = target.json()["id"]

    response = await client.post(
        "/api/transfers",
        json={"source_id": source_id, "target_id": target_id, "amount": "25.00"},
    )

    assert response.status_code == 201
    assert (await client.get(f"/api/accounts/{source_id}")).json()["balance"] == "75.00"
    assert (await client.get(f"/api/accounts/{target_id}")).json()["balance"] == "25.00"
    assert len((await client.get("/api/ledger")).json()) == 1


async def test_failed_transfer_endpoint_leaves_the_database_untouched(
    client: httpx.AsyncClient, bank: BankService
):
    source = await bank.open_account("alice", Decimal("10.00"))
    target = await bank.open_account("bob", Decimal("10.00"))

    response = await client.post(
        "/api/transfers",
        json={"source_id": source.id, "target_id": target.id, "amount": "99.00"},
    )

    assert response.status_code == 409
    assert (await client.get("/api/ledger")).json() == []
    assert (await client.get(f"/api/accounts/{source.id}")).json()["balance"] == "10.00"


async def test_unknown_account_returns_not_found(client: httpx.AsyncClient):
    response = await client.get("/api/accounts/4242")
    assert response.status_code == 404


async def test_a_duplicate_owner_is_a_conflict_not_a_crash(client: httpx.AsyncClient):
    """The unique index on owner is the check, so the refusal arrives as an
    IntegrityError out of the flush and has to reach the caller as a 409."""
    await client.post("/api/accounts", json={"owner": "alice", "initial_balance": "1.00"})

    response = await client.post(
        "/api/accounts", json={"owner": "alice", "initial_balance": "1.00"}
    )

    assert response.status_code == 409
    assert len((await client.get("/api/accounts")).json()) == 1


async def test_an_owner_longer_than_the_column_is_rejected(client: httpx.AsyncClient):
    response = await client.post(
        "/api/accounts", json={"owner": "x" * 200, "initial_balance": "1.00"}
    )

    assert response.status_code == 422


async def test_an_account_id_outside_the_column_range_is_rejected(
    client: httpx.AsyncClient,
):
    """id is an int4. A larger number is a malformed request, not a missing account,
    and it used to reach Postgres and come back as 'integer out of range'."""
    response = await client.get("/api/accounts/99999999999999")

    assert response.status_code == 422


async def test_a_sub_cent_amount_is_rejected(client: httpx.AsyncClient, bank: BankService):
    source = await bank.open_account("alice", Decimal("100.00"))
    target = await bank.open_account("bob", Decimal("0.00"))

    response = await client.post(
        "/api/transfers",
        json={"source_id": source.id, "target_id": target.id, "amount": "0.005"},
    )

    assert response.status_code == 400
    assert (await client.get(f"/api/accounts/{target.id}")).json()["balance"] == "0.00"


async def test_an_amount_too_large_for_the_column_is_rejected(
    client: httpx.AsyncClient, bank: BankService
):
    account = await bank.open_account("alice", Decimal("100.00"))

    response = await client.post(
        f"/api/accounts/{account.id}/deposit", json={"amount": "1e30"}
    )

    assert response.status_code == 400
    assert (await client.get(f"/api/accounts/{account.id}")).json()["balance"] == "100.00"


async def test_a_request_that_cannot_get_a_connection_is_unavailable_not_a_crash(
    client: httpx.AsyncClient, bank: BankService, monkeypatch: pytest.MonkeyPatch
):
    """lock_timeout bounds the wait for a row and arrives as an OperationalError. The
    wait for a connection out of the pool does not: SQLAlchemy raises its own
    TimeoutError, which is not an OperationalError, so it used to miss the 503 handler
    and leave the caller a 500 for a queue that was merely full."""
    account = await bank.open_account("alice", Decimal("100.00"))
    one_connection = create_async_engine(
        DATABASE_URL,
        pool_size=1,
        max_overflow=0,
        pool_timeout=1,
        connect_args={"options": TIMEOUTS},
    )
    monkeypatch.setattr(tx, "session_factory", async_sessionmaker(one_connection))
    holding = asyncio.Event()

    @transactional
    async def hold_the_only_connection() -> None:
        await bank.list_accounts()
        holding.set()
        await asyncio.sleep(5)

    hog = asyncio.create_task(hold_the_only_connection())
    await holding.wait()
    try:
        response = await client.get(f"/api/accounts/{account.id}")
        assert response.status_code == 503
    finally:
        hog.cancel()
        try:
            await hog
        except BaseException:
            pass
        await one_connection.dispose()


async def test_a_non_finite_amount_is_rejected_by_the_request_model(
    client: httpx.AsyncClient, bank: BankService
):
    """NaN and Infinity never reach the service: the request model refuses them, so
    they are a 422 and not the 400 every other bad amount gets. _check_money() still
    refuses them for a caller that reaches the service directly."""
    account = await bank.open_account("alice", Decimal("100.00"))

    for amount in ("NaN", "Infinity", "-Infinity"):
        response = await client.post(
            f"/api/accounts/{account.id}/deposit", json={"amount": amount}
        )
        assert response.status_code == 422, amount

    assert (await client.get(f"/api/accounts/{account.id}")).json()["balance"] == "100.00"


async def test_a_poisoned_transaction_reaching_the_controller_names_its_cause(
    client: httpx.AsyncClient, bank: BankService, monkeypatch: pytest.MonkeyPatch
):
    """UnexpectedRollback means the service swallowed a failure it should not have,
    which is a bug and a 500. Without a handler it was an opaque 'Internal Server
    Error' that threw away the diagnosis the boundary worked to produce."""
    account = await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def swallowing_deposit(account_id: int, amount: Decimal):
        try:
            await bank.withdraw(account_id, Decimal("999.00"))
        except InsufficientFunds:
            pass
        return await bank.get_account(account_id)

    monkeypatch.setattr(controller.service, "deposit", swallowing_deposit)

    response = await client.post(
        f"/api/accounts/{account.id}/deposit", json={"amount": "1.00"}
    )

    assert response.status_code == 500
    assert response.json()["cause"].startswith("InsufficientFunds")
    assert (await client.get(f"/api/accounts/{account.id}")).json()["balance"] == "10.00"


async def test_the_how_it_works_page_shows_the_decorator_that_ships(
    client: httpx.AsyncClient,
):
    """The page annotates tx.py line by line, so a snippet that drifts from the source
    documents a boundary nobody is running. It once showed a recorder that caught
    DBAPIError and not CancelledError, which is a feature this README sells."""
    page = (await client.get("/")).text
    embedded = re.search(r"const TX_CODE = `(.*?)`;", page, re.S).group(1)
    source = Path(inspect.getsourcefile(tx)).read_text()

    assert source.rstrip("\n").endswith(embedded)
    assert embedded.startswith("def _running_task()")


async def test_a_taskgroup_inside_a_boundary_names_its_refusal(
    client: httpx.AsyncClient, bank: BankService, monkeypatch: pytest.MonkeyPatch
):
    """A TaskGroup is the shape fan-out takes in modern async code, and it wraps what
    its children raise. CrossTaskTransaction arrives inside an ExceptionGroup, which is
    not an instance of it, so the handler that exists to name the diagnosis never
    matched and the caller got an opaque 'Internal Server Error' instead."""
    account = await bank.open_account("alice", Decimal("10.00"))

    @transactional
    async def grouped_deposit(account_id: int, amount: Decimal):
        async with asyncio.TaskGroup() as group:
            group.create_task(bank.list_accounts())

    monkeypatch.setattr(controller.service, "deposit", grouped_deposit)

    response = await client.post(
        f"/api/accounts/{account.id}/deposit", json={"amount": "1.00"}
    )

    assert response.status_code == 500
    assert "CrossTaskTransaction" in response.json()["cause"]
    assert (await client.get(f"/api/accounts/{account.id}")).json()["balance"] == "10.00"


async def test_a_blank_owner_is_refused_by_the_layer_that_can_see_it(
    client: httpx.AsyncClient,
):
    """min_length on the request model refuses the empty string, so that one is a 422.
    A string of spaces is a value the schema can hold and an account nobody can name, so
    it is the service that refuses it and a 400, the same way a sub-cent amount is."""
    assert (
        await client.post("/api/accounts", json={"owner": "", "initial_balance": "1.00"})
    ).status_code == 422

    response = await client.post(
        "/api/accounts", json={"owner": "   ", "initial_balance": "1.00"}
    )

    assert response.status_code == 400
    assert (await client.get("/api/accounts")).json() == []


async def test_the_readme_shows_the_decorator_that_ships():
    """The README prints the mechanism in full and calls it that, so a block that has
    drifted from the source documents a boundary nobody is running. The How it works
    page drifted exactly that way once, which is why both are pinned now."""
    source = Path(inspect.getsourcefile(tx))
    readme = (source.parent.parent / "README.md").read_text()
    blocks = re.findall(r"```python\n(.*?)```", readme, re.S)

    assert len(blocks) == 2
    for block in blocks:
        assert block in source.read_text(), block.splitlines()[0]
