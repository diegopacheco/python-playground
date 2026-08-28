import base64
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

USERS = [
    {"id": 1, "name": "ada", "lang": "python"},
    {"id": 2, "name": "linus", "lang": "c"},
    {"id": 3, "name": "guido", "lang": "python"},
    {"id": 4, "name": "graydon", "lang": "rust"},
]

CREDENTIALS = "Basic " + base64.b64encode(b"admin:secret").decode()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "httpx2-poc"

    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        url = urlparse(self.path)
        params = parse_qs(url.query)
        if url.path == "/health":
            self.send_json(200, {"status": "ok"})
        elif url.path == "/users":
            self.send_json(200, {"users": USERS})
        elif url.path == "/stream":
            self.send_chunks(int(params.get("lines", ["5"])[0]))
        elif url.path == "/events":
            self.send_events(int(params.get("count", ["3"])[0]))
        elif url.path == "/delay":
            time.sleep(float(params.get("seconds", ["1"])[0]))
            self.send_json(200, {"status": "ok"})
        elif url.path == "/secure":
            self.send_secure()
        elif url.path.startswith("/status/"):
            self.send_json(int(url.path.rsplit("/", 1)[1]), {"path": url.path})
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self):
        if urlparse(self.path).path != "/echo":
            self.send_json(404, {"error": "not found"})
            return
        self.send_json(
            200,
            {
                "received": self.read_json(),
                "agent": self.headers.get("user-agent", ""),
            },
        )

    def do_QUERY(self):
        if urlparse(self.path).path != "/search":
            self.send_json(404, {"error": "not found"})
            return
        criteria = self.read_json()
        matches = [u for u in USERS if all(u.get(k) == v for k, v in criteria.items())]
        self.send_json(200, {"matches": matches})

    def send_secure(self):
        if self.headers.get("authorization") != CREDENTIALS:
            self.send_json(
                401,
                {"error": "unauthorized"},
                [("www-authenticate", 'Basic realm="httpx2-poc"')],
            )
            return
        self.send_json(200, {"user": "admin", "scope": "poc"})

    def read_json(self):
        size = int(self.headers.get("content-length", 0))
        return json.loads(self.rfile.read(size)) if size else {}

    def send_json(self, status, payload, extra_headers=()):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        for name, value in extra_headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def start_chunked(self, content_type):
        self.send_response(200)
        self.send_header("content-type", content_type)
        self.send_header("transfer-encoding", "chunked")
        self.end_headers()

    def write_chunk(self, text):
        data = text.encode()
        self.wfile.write(b"%x\r\n%s\r\n" % (len(data), data))
        self.wfile.flush()

    def end_chunked(self):
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()

    def send_chunks(self, lines):
        self.start_chunked("text/plain; charset=utf-8")
        for seq in range(1, lines + 1):
            self.write_chunk(f"line {seq}\n")
        self.end_chunked()

    def send_events(self, count):
        self.start_chunked("text/event-stream")
        for seq in range(1, count + 1):
            payload = json.dumps({"seq": seq, "user": USERS[(seq - 1) % len(USERS)]})
            self.write_chunk(f"event: tick\nid: {seq}\ndata: {payload}\n\n")
        self.end_chunked()


def build(port=8080, host="127.0.0.1"):
    return ThreadingHTTPServer((host, port), Handler)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = build(port)
    print(f"httpx2-poc server listening on http://127.0.0.1:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
