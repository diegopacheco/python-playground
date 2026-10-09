import json
import unittest

from api import TaskApi
from tasks import TaskStore
from web import Json, Request, Response, Router


def send(router: Router, method: str, path: str, payload: Json = None, **query: str) -> Response:
    body = b"" if payload is None else json.dumps(payload).encode()
    return router.dispatch(Request(method, path, query, body))


class TaskApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.router = TaskApi(TaskStore()).router()

    def test_created_task_can_be_read_back_by_its_id(self) -> None:
        created = send(self.router, "POST", "/tasks", {"title": "write the report"})
        self.assertEqual(created.status, 201)
        self.assertEqual(created.payload, {"id": 1, "title": "write the report", "done": False})
        self.assertEqual(send(self.router, "GET", "/tasks/1").payload, created.payload)

    def test_every_task_gets_its_own_id(self) -> None:
        first = send(self.router, "POST", "/tasks", {"title": "first"})
        second = send(self.router, "POST", "/tasks", {"title": "second"})
        self.assertEqual(first.payload, {"id": 1, "title": "first", "done": False})
        self.assertEqual(second.payload, {"id": 2, "title": "second", "done": False})

    def test_an_id_is_never_reused_after_a_delete(self) -> None:
        send(self.router, "POST", "/tasks", {"title": "first"})
        send(self.router, "DELETE", "/tasks/1")
        again = send(self.router, "POST", "/tasks", {"title": "second"})
        self.assertEqual(again.payload, {"id": 2, "title": "second", "done": False})

    def test_title_is_stored_without_surrounding_spaces(self) -> None:
        created = send(self.router, "POST", "/tasks", {"title": "  call the bank  "})
        self.assertEqual(created.payload, {"id": 1, "title": "call the bank", "done": False})

    def test_a_task_without_a_usable_title_is_rejected_and_not_stored(self) -> None:
        payloads: tuple[Json, ...] = ({}, {"title": "   "}, {"title": 7}, {"done": True}, ["title"], "title")
        for payload in payloads:
            with self.subTest(payload=payload):
                self.assertEqual(send(self.router, "POST", "/tasks", payload).status, 400)
        self.assertEqual(send(self.router, "GET", "/tasks").payload, [])

    def test_done_must_be_a_real_boolean(self) -> None:
        for done in ("yes", 1, None):
            with self.subTest(done=done):
                rejected = send(self.router, "POST", "/tasks", {"title": "pay rent", "done": done})
                self.assertEqual(rejected.status, 400)

    def test_broken_json_is_a_client_error(self) -> None:
        rejected = self.router.dispatch(Request("POST", "/tasks", {}, b"{title"))
        self.assertEqual(rejected.status, 400)
        self.assertEqual(rejected.payload, {"error": "body is not valid JSON"})

    def test_update_replaces_title_and_done(self) -> None:
        send(self.router, "POST", "/tasks", {"title": "draft"})
        updated = send(self.router, "PUT", "/tasks/1", {"title": "final", "done": True})
        self.assertEqual(updated.status, 200)
        self.assertEqual(send(self.router, "GET", "/tasks/1").payload, {"id": 1, "title": "final", "done": True})

    def test_update_never_creates_a_missing_task(self) -> None:
        missing = send(self.router, "PUT", "/tasks/9", {"title": "ghost"})
        self.assertEqual(missing.status, 404)
        self.assertEqual(send(self.router, "GET", "/tasks").payload, [])

    def test_deleted_task_is_gone(self) -> None:
        send(self.router, "POST", "/tasks", {"title": "temporary"})
        deleted = send(self.router, "DELETE", "/tasks/1")
        self.assertEqual(deleted.status, 204)
        self.assertIsNone(deleted.payload)
        self.assertEqual(send(self.router, "GET", "/tasks/1").status, 404)
        self.assertEqual(send(self.router, "DELETE", "/tasks/1").status, 404)

    def test_list_filters_by_done(self) -> None:
        send(self.router, "POST", "/tasks", {"title": "open"})
        send(self.router, "POST", "/tasks", {"title": "closed", "done": True})
        everything = send(self.router, "GET", "/tasks").payload
        self.assertEqual(
            everything,
            [{"id": 1, "title": "open", "done": False}, {"id": 2, "title": "closed", "done": True}],
        )
        self.assertEqual(send(self.router, "GET", "/tasks", done="true").payload, [{"id": 2, "title": "closed", "done": True}])
        self.assertEqual(send(self.router, "GET", "/tasks", done="false").payload, [{"id": 1, "title": "open", "done": False}])

    def test_unknown_done_filter_is_rejected(self) -> None:
        self.assertEqual(send(self.router, "GET", "/tasks", done="maybe").status, 400)

    def test_non_numeric_id_is_not_found(self) -> None:
        self.assertEqual(send(self.router, "GET", "/tasks/abc").status, 404)

    def test_unknown_path_is_not_found(self) -> None:
        self.assertEqual(send(self.router, "GET", "/users").status, 404)
        self.assertEqual(send(self.router, "GET", "/tasks/1/extra").status, 404)

    def test_known_path_with_wrong_method_is_not_allowed(self) -> None:
        self.assertEqual(send(self.router, "DELETE", "/tasks").status, 405)
        self.assertEqual(send(self.router, "POST", "/tasks/1").status, 405)

    def test_health_reports_how_many_tasks_exist(self) -> None:
        send(self.router, "POST", "/tasks", {"title": "one"})
        health = send(self.router, "GET", "/health")
        self.assertEqual(health.status, 200)
        self.assertEqual(health.payload, {"status": "up", "tasks": 1})
