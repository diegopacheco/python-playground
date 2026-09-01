import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

import db

MAX_BODY = 1 << 20
DEFAULT_LIMIT = 10


class BadRequest(Exception):
    pass


def encode(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"cannot serialize {type(value).__name__}")


def one(params, name):
    values = params.get(name)
    return values[0] if values else None


def parse_filters(params):
    raw = one(params, "contains")
    contains = None
    if raw:
        try:
            contains = json.loads(raw)
        except json.JSONDecodeError as error:
            raise BadRequest(f"contains is not valid json: {error}") from error
        if not isinstance(contains, dict):
            raise BadRequest("contains must be a json object")
    any_keys = one(params, "anyKey")
    has_any_key = [k for k in any_keys.split(",") if k] if any_keys else None
    limit = one(params, "limit") or DEFAULT_LIMIT
    try:
        limit = int(limit)
    except ValueError as error:
        raise BadRequest("limit must be an integer") from error
    if limit < 1 or limit > 1000:
        raise BadRequest("limit must be between 1 and 1000")
    return contains, one(params, "key"), has_any_key, limit


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "gin-poc"

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {fmt % args}", flush=True)

    def reply(self, status, payload):
        body = json.dumps(payload, default=encode).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            raise BadRequest("body is required")
        if length > MAX_BODY:
            raise BadRequest("body is too large")
        try:
            return json.loads(self.rfile.read(length))
        except json.JSONDecodeError as error:
            raise BadRequest(f"body is not valid json: {error}") from error

    def do_GET(self):
        url = urlparse(self.path)
        params = parse_qs(url.query)
        try:
            if url.path == "/health":
                self.reply(200, {"status": "ok", "documents": db.count()})
            elif url.path == "/documents":
                self.list_documents(params)
            elif url.path == "/explain":
                self.explain_documents(params)
            elif url.path.startswith("/documents/"):
                self.get_document(url.path.removeprefix("/documents/"))
            else:
                self.reply(404, {"error": "unknown route"})
        except BadRequest as error:
            self.reply(400, {"error": str(error)})

    def do_POST(self):
        url = urlparse(self.path)
        try:
            if url.path != "/documents":
                self.reply(404, {"error": "unknown route"})
                return
            payload = self.read_body()
            name = payload.get("name")
            data = payload.get("data")
            if not isinstance(name, str) or not name:
                raise BadRequest("name must be a non empty string")
            if not isinstance(data, dict):
                raise BadRequest("data must be a json object")
            self.reply(201, db.insert(name, data))
        except BadRequest as error:
            self.reply(400, {"error": str(error)})

    def list_documents(self, params):
        contains, key, any_key, limit = parse_filters(params)
        rows = db.search(contains, key, any_key, limit)
        self.reply(200, {"count": len(rows), "documents": rows})

    def explain_documents(self, params):
        contains, key, any_key, limit = parse_filters(params)
        plan = db.explain(contains, key, any_key, limit)
        indexes = db.indexes_used(plan["Plan"])
        self.reply(
            200,
            {
                "indexes": indexes,
                "ginIndexUsed": any(i.endswith("_gin") for i in indexes),
                "executionTimeMs": plan.get("Execution Time"),
                "plan": plan,
            },
        )

    def get_document(self, raw_id):
        if not raw_id.isdigit():
            raise BadRequest("id must be a number")
        row = db.by_id(int(raw_id))
        if row is None:
            self.reply(404, {"error": "document not found"})
            return
        self.reply(200, row)
