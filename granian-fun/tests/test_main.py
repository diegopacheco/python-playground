import asyncio
import json
import unittest
from dataclasses import dataclass, field

from main import app


@dataclass(frozen=True)
class FakeScope:
    method: str
    path: str
    query_string: str = ""


@dataclass
class FakeTransport:
    body: bytes = b""
    status: int = 0
    headers: list[tuple[str, str]] = field(default_factory=list)
    sent: str | None = None

    async def __call__(self) -> bytes:
        return self.body

    def response_empty(self, status: int, headers: list[tuple[str, str]]) -> None:
        self.status = status
        self.headers = headers

    def response_str(self, status: int, headers: list[tuple[str, str]], body: str) -> None:
        self.status = status
        self.headers = headers
        self.sent = body


def call(method: str, path: str, query_string: str = "", body: bytes = b"") -> FakeTransport:
    transport = FakeTransport(body)
    asyncio.run(app(FakeScope(method, path, query_string), transport))
    return transport


class RsgiAdapterTest(unittest.TestCase):
    def test_request_body_and_query_string_reach_the_api_and_the_reply_is_json(self) -> None:
        created = call("POST", "/tasks", body=b'{"title": "ship it", "done": true}')
        self.assertEqual(created.status, 201)
        self.assertEqual(created.headers, [("content-type", "application/json")])
        assert created.sent is not None
        task = json.loads(created.sent)
        self.assertEqual(task["title"], "ship it")

        listed = call("GET", "/tasks", "done=true")
        assert listed.sent is not None
        self.assertIn(task, json.loads(listed.sent))
        pending = call("GET", "/tasks", "done=false")
        assert pending.sent is not None
        self.assertNotIn(task, json.loads(pending.sent))

        deleted = call("DELETE", f"/tasks/{task['id']}")
        self.assertEqual(deleted.status, 204)
        self.assertIsNone(deleted.sent)

    def test_errors_are_sent_as_json_with_their_status(self) -> None:
        missing = call("GET", "/nowhere")
        self.assertEqual(missing.status, 404)
        assert missing.sent is not None
        self.assertEqual(json.loads(missing.sent), {"error": "/nowhere was not found"})
