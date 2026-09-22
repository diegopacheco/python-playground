import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from onnx_router.paths import STATIC_DIR
from onnx_router.router import DEFAULT_MODEL, ROUTES, Router


def make_handler(router: Router) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/":
                self.send_body(HTTPStatus.OK, "text/html", (STATIC_DIR / "index.html").read_bytes())
            elif self.path == "/api/routes":
                body = {"routes": ROUTES, "default": DEFAULT_MODEL, "threshold": router.threshold}
                self.send_json(HTTPStatus.OK, body)
            elif self.path == "/api/health":
                self.send_json(HTTPStatus.OK, {"status": "up"})
            else:
                self.send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

        def do_POST(self) -> None:
            if self.path != "/api/route":
                self.send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length) or b"{}")
                decision = router.route(str(payload.get("prompt", "")))
            except (ValueError, AttributeError) as error:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
                return
            self.send_json(HTTPStatus.OK, decision.to_dict())

        def send_json(self, status: HTTPStatus, body: dict) -> None:
            self.send_body(status, "application/json", json.dumps(body).encode())

        def send_body(self, status: HTTPStatus, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def serve(port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(Router()))


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    server = serve(port)
    print(f"onnx-router listening on http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
