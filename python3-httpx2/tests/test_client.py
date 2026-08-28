import asyncio

import httpx2
import pytest

import client


def test_health_reports_ok(http):
    assert client.health(http) == {"status": "ok"}


def test_base_url_and_default_headers_are_applied(http):
    body = client.echo(http, {"ping": True})

    assert body["received"] == {"ping": True}
    assert body["agent"] == "httpx2-poc"


def test_query_method_sends_a_body_and_filters_server_side(http):
    matches = client.search(http, {"lang": "python"})

    assert [u["name"] for u in matches] == ["ada", "guido"]


def test_query_is_sent_as_the_query_verb_not_as_a_get(http):
    response = http.query("/search", json={"lang": "rust"})

    assert response.request.method == "QUERY"
    assert [u["name"] for u in response.json()["matches"]] == ["graydon"]


def test_streaming_yields_chunks_without_buffering_the_body(http):
    with http.stream("GET", "/stream", params={"lines": 3}) as response:
        assert "content-length" not in response.headers
        with pytest.raises(httpx2.ResponseNotRead):
            response.text
        assert [line for line in response.iter_lines() if line] == [
            "line 1",
            "line 2",
            "line 3",
        ]


def test_sse_decodes_event_name_id_and_json_data(http):
    with http.sse("/events", params={"count": 2}) as source:
        received = list(source)

    assert [e.event for e in received] == ["tick", "tick"]
    assert [e.id for e in received] == ["1", "2"]
    assert [e.json()["seq"] for e in received] == [1, 2]


def test_secure_endpoint_rejects_missing_credentials(http):
    assert http.get("/secure").status_code == 401


def test_basic_auth_unlocks_the_secure_endpoint(http):
    assert client.secure(http, "admin", "secret") == {"user": "admin", "scope": "poc"}


def test_error_status_raises_only_through_raise_for_status(http):
    response = http.get("/status/503")

    assert response.is_server_error
    assert client.status_error(http, 503) == 503


def test_read_timeout_is_enforced_per_request(http):
    assert client.read_timeout(http, 1.0) is True


def test_async_client_resolves_every_concurrent_request(base_url):
    assert asyncio.run(client.concurrent_health(base_url, 5)) == ["ok"] * 5


def test_mock_transport_exercises_the_client_without_a_server():
    def handler(request):
        assert request.url.path == "/health"
        return httpx2.Response(200, json={"status": "mocked"})

    transport = httpx2.MockTransport(handler)
    with httpx2.Client(base_url="http://testserver", transport=transport) as mocked:
        assert client.health(mocked) == {"status": "mocked"}
