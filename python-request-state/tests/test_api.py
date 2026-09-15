import uuid

from db import SUPER_MARIO_BROS

PAYLOAD = {
    "name": "Metroid",
    "description": "Samus explores Zebes",
    "release_year": 1986,
    "image_url": "https://example.org/metroid.png",
}


def test_every_response_carries_a_unique_request_id_from_request_state(client):
    first = client.get("/api/games").headers["X-Request-ID"]
    second = client.get("/api/games").headers["X-Request-ID"]
    assert uuid.UUID(first) and uuid.UUID(second)
    assert first != second


def test_not_found_body_echoes_the_request_id_of_the_header(client):
    response = client.get(f"/api/games/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["request_id"] == response.headers["X-Request-ID"]


def test_full_crud_cycle(client):
    created = client.post("/api/games", json=PAYLOAD)
    assert created.status_code == 201
    game_id = created.json()["id"]

    assert client.get(f"/api/games/{game_id}").json()["name"] == "Metroid"

    updated = client.put(f"/api/games/{game_id}", json={**PAYLOAD, "name": "Super Metroid"})
    assert updated.json()["name"] == "Super Metroid"

    assert {g["id"] for g in client.get("/api/games").json()} == {SUPER_MARIO_BROS["id"], game_id}

    assert client.delete(f"/api/games/{game_id}").status_code == 204
    assert client.get(f"/api/games/{game_id}").status_code == 404


def test_invalid_payloads_are_rejected(client):
    assert client.post("/api/games", json={**PAYLOAD, "release_year": 1800}).status_code == 422
    assert client.post("/api/games", json={**PAYLOAD, "name": "   "}).status_code == 422
    assert client.post("/api/games", json={**PAYLOAD, "image_url": "ftp://x"}).status_code == 422
    assert client.get("/api/games/42").status_code == 422


def test_ui_is_served_from_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "app.js" in response.text
