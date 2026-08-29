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
