from sqlalchemy import text

from db import engine

ORDER = {
    "status": "paid",
    "total": 249.9,
    "customer": {"id": 42, "tier": "gold"},
    "items": [{"sku": "kbd-01", "qty": 1}],
    "gift": False,
    "coupon": None,
}


def create(client, name, data):
    response = client.post("/api/documents", json={"name": name, "data": data})
    assert response.status_code == 201, response.text
    return response.json()


def test_column_is_jsonb_not_text(client):
    with engine.connect() as connection:
        data_type = connection.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = 'documents' AND column_name = 'data'"
            )
        ).scalar_one()
    assert data_type == "jsonb"


def test_roundtrip_preserves_types_and_nesting(client):
    created = create(client, "order-1001", ORDER)
    stored = client.get("/api/documents").json()[0]["data"]

    assert created["data"] == ORDER
    assert stored == ORDER
    assert isinstance(stored["customer"]["id"], int)
    assert isinstance(stored["total"], float)
    assert stored["gift"] is False
    assert stored["coupon"] is None
    assert stored["items"][0]["sku"] == "kbd-01"


def test_containment_filter_selects_only_matching_documents(client):
    create(client, "order-1001", ORDER)
    create(client, "order-1002", {**ORDER, "status": "refunded"})

    paid = client.get("/api/documents", params={"contains": '{"status": "paid"}'}).json()

    assert [row["name"] for row in paid] == ["order-1001"]


def test_containment_matches_nested_subtree(client):
    create(client, "order-1001", ORDER)
    create(client, "order-1002", {**ORDER, "customer": {"id": 7, "tier": "silver"}})

    gold = client.get(
        "/api/documents", params={"contains": '{"customer": {"tier": "gold"}}'}
    ).json()

    assert [row["name"] for row in gold] == ["order-1001"]


def test_containment_ignores_unindexed_keys_and_returns_empty(client):
    create(client, "order-1001", ORDER)

    missing = client.get(
        "/api/documents", params={"contains": '{"status": "cancelled"}'}
    ).json()

    assert missing == []


def test_invalid_containment_filter_is_rejected(client):
    assert client.get("/api/documents", params={"contains": "{oops"}).status_code == 400
    assert client.get("/api/documents", params={"contains": "[1,2]"}).status_code == 400


def test_update_replaces_the_whole_document(client):
    created = create(client, "order-1001", ORDER)

    updated = client.put(
        f"/api/documents/{created['id']}",
        json={"name": "order-1001", "data": {"status": "shipped"}},
    )

    assert updated.status_code == 200
    assert updated.json()["data"] == {"status": "shipped"}
    assert client.get("/api/documents").json()[0]["data"] == {"status": "shipped"}


def test_delete_removes_the_document(client):
    created = create(client, "order-1001", ORDER)

    assert client.delete(f"/api/documents/{created['id']}").status_code == 204
    assert client.get("/api/documents").json() == []
    assert client.delete(f"/api/documents/{created['id']}").status_code == 404


def test_rejects_document_without_a_name(client):
    response = client.post("/api/documents", json={"name": "", "data": ORDER})

    assert response.status_code == 422
