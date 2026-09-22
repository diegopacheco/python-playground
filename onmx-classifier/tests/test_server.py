import json
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from http.server import ThreadingHTTPServer

import pytest

from onnx_router.router import ROUTES, Router
from onnx_router.server import make_handler


@pytest.fixture
def base_url(router: Router) -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(router))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def post(url: str, body: dict) -> tuple[int, dict]:
    request = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def test_route_endpoint_returns_the_chosen_model(base_url: str) -> None:
    status, body = post(f"{base_url}/api/route", {"prompt": "write a poem about the stars"})
    assert status == 200
    assert body["model"] == ROUTES["creative"]


def test_route_endpoint_rejects_empty_prompt_with_400(base_url: str) -> None:
    status, body = post(f"{base_url}/api/route", {"prompt": ""})
    assert status == 400
    assert "empty" in body["error"]


def test_routes_endpoint_exposes_the_routing_table(base_url: str) -> None:
    with urllib.request.urlopen(f"{base_url}/api/routes") as response:
        assert json.loads(response.read())["routes"] == ROUTES


def test_ui_is_served_at_root(base_url: str) -> None:
    with urllib.request.urlopen(base_url) as response:
        assert b"ONNX Model Router" in response.read()
