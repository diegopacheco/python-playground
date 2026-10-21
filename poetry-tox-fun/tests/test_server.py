import json
import threading
from collections.abc import Iterator
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from notes_app.server import MAX_REQUEST_BYTES, NotesServer
from notes_app.store import NoteStore


@pytest.fixture
def base_url() -> Iterator[str]:
    server = NotesServer(("127.0.0.1", 0), NoteStore())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def call(url: str, method: str = "GET", body: bytes | None = None) -> tuple[int, object]:
    request = Request(url, data=body, method=method, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except HTTPError as error:
        return error.code, json.loads(error.read())


def test_note_lifecycle_create_read_list_delete(base_url: str) -> None:
    status, created = call(f"{base_url}/api/notes", "POST", b'{"title": "ship it", "body": "friday"}')
    assert status == 201
    assert isinstance(created, dict)
    note_url = f"{base_url}/api/notes/{created['id']}"

    assert call(note_url) == (200, created)
    assert call(f"{base_url}/api/notes") == (200, [created])
    assert call(note_url, "DELETE") == (204, None)
    assert call(note_url) == (404, {"error": "not found"})
    assert call(f"{base_url}/api/notes") == (200, [])


@pytest.mark.parametrize(
    ("body", "error"),
    [
        (b"not json", "body must be valid json"),
        (b"[1, 2]", "body must be a json object"),
        (b'{"body": "no title"}', "title must be a string"),
        (b'{"title": "   "}', "title is required"),
        (b"x" * (MAX_REQUEST_BYTES + 1), f"body must have at most {MAX_REQUEST_BYTES} bytes"),
    ],
)
def test_bad_input_answers_400_with_reason_and_stores_nothing(base_url: str, body: bytes, error: str) -> None:
    assert call(f"{base_url}/api/notes", "POST", body) == (400, {"error": error})
    assert call(f"{base_url}/api/notes") == (200, [])


def test_unknown_routes_and_missing_notes_answer_404(base_url: str) -> None:
    assert call(f"{base_url}/nope")[0] == 404
    assert call(f"{base_url}/api/notes/1", "DELETE")[0] == 404
    assert call(f"{base_url}/api/other", "POST", b"{}")[0] == 404


def test_root_serves_the_html_ui_and_health_reports_up(base_url: str) -> None:
    with urlopen(f"{base_url}/") as response:
        assert response.headers["Content-Type"].startswith("text/html")
        assert b"<title>Notes</title>" in response.read()
    assert call(f"{base_url}/health") == (200, {"status": "UP"})
