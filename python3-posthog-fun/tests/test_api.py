import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(posthog=None))


def rent(client: TestClient, dvd_id: str, user_id: str = "diego"):
    return client.post("/rentals", json={"dvd_id": dvd_id, "user_id": user_id})


def test_catalog_marks_a_rented_dvd_as_unavailable(client):
    rent(client, "dvd-002")

    by_id = {dvd["dvd_id"]: dvd for dvd in client.get("/dvds").json()}

    assert by_id["dvd-002"]["available"] is False
    assert by_id["dvd-001"]["available"] is True


def test_renting_returns_the_rental_with_its_deadline(client):
    response = rent(client, "dvd-002")

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "The Matrix"
    assert body["status"] == "active"
    assert body["due_at"] > body["rented_at"]


def test_renting_a_dvd_that_is_out_conflicts(client):
    rent(client, "dvd-002")

    assert rent(client, "dvd-002", "someone-else").status_code == 409


def test_unknown_dvd_and_rental_are_not_found(client):
    assert rent(client, "nope").status_code == 404
    assert client.post("/rentals/nope/return").status_code == 404


def test_returning_a_rental_closes_it(client):
    rental_id = rent(client, "dvd-002").json()["rental_id"]

    body = client.post(f"/rentals/{rental_id}/return").json()

    assert body["status"] == "returned"
    assert body["returned_at"] is not None


def test_top_rented_endpoint_ranks_the_busiest_titles(client):
    for _ in range(2):
        rental_id = rent(client, "dvd-002").json()["rental_id"]
        client.post(f"/rentals/{rental_id}/return")
    rental_id = rent(client, "dvd-004").json()["rental_id"]
    client.post(f"/rentals/{rental_id}/return")

    ranked = client.get("/stats/top-rented").json()

    assert [(row["rank"], row["dvd_id"], row["rentals"]) for row in ranked] == [
        (1, "dvd-002", 2),
        (2, "dvd-004", 1),
    ]


def test_never_rented_endpoint_returns_at_most_five_untouched_titles(client):
    rent(client, "dvd-002")

    rows = client.get("/stats/never-rented").json()

    assert len(rows) == 5
    assert "dvd-002" not in {row["dvd_id"] for row in rows}
    assert all(row["rentals"] == 0 for row in rows)


def test_the_event_feed_shows_what_was_sent_to_posthog(client):
    rent(client, "dvd-002")

    events = client.get("/events").json()

    assert events[0]["event"] == "dvd_rented"
    assert events[0]["distinct_id"] == "diego"
    assert events[0]["properties"]["title"] == "The Matrix"


def test_health_reports_the_timing_knobs_used_for_testing(client):
    body = client.get("/health").json()

    assert body["status"] == "ok"
    assert body["rental_period_seconds"] > 0
    assert body["rollup_interval_minutes"] > 0
    assert body["deadline_scan_seconds"] > 0
