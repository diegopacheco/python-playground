import json
import re
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from notes_app.page import PAGE
from notes_app.store import NoteError, NoteStore

NOTE_PATH = re.compile(r"^/api/notes/(\d+)$")
MAX_REQUEST_BYTES = 16_384


class NotesServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], store: NoteStore) -> None:
        super().__init__(address, NotesHandler)
        self.store = store


class NotesHandler(BaseHTTPRequestHandler):
    @property
    def store(self) -> NoteStore:
        assert isinstance(self.server, NotesServer)
        return self.server.store

    def do_GET(self) -> None:
        match = NOTE_PATH.match(self.path)
        if self.path == "/":
            self._send(HTTPStatus.OK, PAGE.encode(), "text/html; charset=utf-8")
        elif self.path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "UP"})
        elif self.path == "/api/notes":
            self._send_json(HTTPStatus.OK, [asdict(note) for note in self.store.all()])
        elif match and (note := self.store.get(int(match[1]))):
            self._send_json(HTTPStatus.OK, asdict(note))
        else:
            self._send_error(HTTPStatus.NOT_FOUND, "not found")

    def do_POST(self) -> None:
        if self.path != "/api/notes":
            self._send_error(HTTPStatus.NOT_FOUND, "not found")
            return
        try:
            payload = self._read_json()
            note = self.store.add(payload.get("title"), payload.get("body", ""))
        except NoteError as error:
            self._send_error(HTTPStatus.BAD_REQUEST, str(error))
            return
        self._send_json(HTTPStatus.CREATED, asdict(note))

    def do_DELETE(self) -> None:
        match = NOTE_PATH.match(self.path)
        if match and self.store.delete(int(match[1])):
            self._send(HTTPStatus.NO_CONTENT, b"", "application/json")
        else:
            self._send_error(HTTPStatus.NOT_FOUND, "not found")

    def _read_json(self) -> dict[str, object]:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError as error:
            raise NoteError("invalid Content-Length") from error
        if length > MAX_REQUEST_BYTES:
            raise NoteError(f"body must have at most {MAX_REQUEST_BYTES} bytes")
        try:
            payload: object = json.loads(self.rfile.read(length) or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise NoteError("body must be valid json") from error
        if not isinstance(payload, dict):
            raise NoteError("body must be a json object")
        return payload

    def _send_error(self, status: HTTPStatus, message: str) -> None:
        self._send_json(status, {"error": message})

    def _send_json(self, status: HTTPStatus, data: object) -> None:
        self._send(status, json.dumps(data).encode(), "application/json")

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
