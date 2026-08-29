from decimal import Decimal

import httpx
import pytest

from controller import app
from service import BankService


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
