import json
import os
import re
import uuid
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = os.environ.get("TASKLY_HOST", "127.0.0.1")
PORT = int(os.environ.get("TASKLY_PORT", "8080"))
STATES = ("pending", "doing", "done")
TASK_PATH = re.compile(r"^/tasks/([^/]+)$")

TASKS = {}


class TasklyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        print(f"{self.command} {self.path} -> {args[1]}")

    def send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def error(self, status, message):
        self.send_json(status, {"message": message})

    def authorized(self):
        header = self.headers.get("Authorization", "")
        if header.startswith("Bearer ") and header[7:].strip():
            return True
        self.error(401, "missing or invalid bearer token")
        return False

    def read_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            return None

    def split_path(self):
        path, _, query = self.path.partition("?")
        params = {}
        for chunk in query.split("&"):
            if "=" in chunk:
                key, value = chunk.split("=", 1)
                params[key] = value
        return path, params

    def do_GET(self):
        path, params = self.split_path()
        if path == "/status":
            self.send_json(200, {"message": "taskly is up"})
            return
        if not self.authorized():
            return
        if path == "/tasks":
            state = params.get("state")
            if state is not None and state not in STATES:
                self.error(400, f"unknown state {state}")
                return
            data = [t for t in TASKS.values() if state is None or t["state"] == state]
            self.send_json(200, {"data": data})
            return
        match = TASK_PATH.match(path)
        if match:
            task = TASKS.get(match.group(1))
            if task is None:
                self.error(404, "task not found")
                return
            self.send_json(200, task)
            return
        self.error(404, "unknown path")

    def do_POST(self):
        path, _ = self.split_path()
        if not self.authorized():
            return
        if path != "/tasks":
            self.error(404, "unknown path")
            return
        body = self.read_body()
        if body is None or not body.get("title"):
            self.error(400, "title is required")
            return
        state = body.get("state", "pending")
        if state not in STATES:
            self.error(400, f"unknown state {state}")
            return
        task = {
            "id": str(uuid.uuid4()),
            "title": body["title"],
            "details": body.get("details"),
            "state": state,
            "created_at": datetime.now(UTC).isoformat(),
        }
        TASKS[task["id"]] = task
        self.send_json(201, task)

    def do_PUT(self):
        path, _ = self.split_path()
        if not self.authorized():
            return
        match = TASK_PATH.match(path)
        if not match:
            self.error(404, "unknown path")
            return
        task = TASKS.get(match.group(1))
        if task is None:
            self.error(404, "task not found")
            return
        body = self.read_body()
        if body is None:
            self.error(400, "invalid body")
            return
        if "state" in body and body["state"] not in STATES:
            self.error(400, f"unknown state {body['state']}")
            return
        for field in ("title", "details", "state"):
            if field in body:
                task[field] = body[field]
        self.send_json(200, task)

    def do_DELETE(self):
        path, _ = self.split_path()
        if not self.authorized():
            return
        match = TASK_PATH.match(path)
        if not match:
            self.error(404, "unknown path")
            return
        task = TASKS.pop(match.group(1), None)
        if task is None:
            self.error(404, "task not found")
            return
        self.send_json(200, task)


def main():
    server = ThreadingHTTPServer((HOST, PORT), TasklyHandler)
    print(f"taskly listening on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("taskly stopping")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
