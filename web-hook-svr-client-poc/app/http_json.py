import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class JsonHandler(BaseHTTPRequestHandler):
    def send_json(self, status: int, body) -> None:
        self.send_bytes(status, json.dumps(body).encode(), "application/json")

    def send_bytes(self, status: int, data: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return {}
        return body if isinstance(body, dict) else {}

    def log_message(self, format, *args):
        print(format % args, flush=True)


def serve(port: int, handler: type[BaseHTTPRequestHandler]) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"listening on http://localhost:{port}", flush=True)
    server.serve_forever()
