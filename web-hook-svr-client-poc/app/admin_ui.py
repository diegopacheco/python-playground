import urllib.error
import urllib.request
from pathlib import Path

from app.config import required
from app.http_json import JsonHandler, serve

INDEX = Path(__file__).parent / "static" / "index.html"


def make_handler(listener_url: str, server_url: str) -> type[JsonHandler]:
    upstreams = {"/api/events": listener_url, "/health": listener_url, "/api/deliveries": server_url}

    class Handler(JsonHandler):
        def do_GET(self) -> None:
            if self.path in ("/", "/index.html"):
                return self.send_bytes(200, INDEX.read_bytes(), "text/html; charset=utf-8")
            if self.path in upstreams:
                return self.proxy(upstreams[self.path])
            self.send_json(404, {"error": "not found"})

        def proxy(self, upstream: str) -> None:
            try:
                with urllib.request.urlopen(upstream + self.path, timeout=5) as response:
                    self.send_bytes(response.status, response.read(), "application/json")
            except (urllib.error.URLError, TimeoutError) as error:
                self.send_json(502, {"error": f"{upstream} unavailable: {error}"})

    return Handler


def main() -> None:
    listener_url = f"http://localhost:{required('LISTENER_PORT')}"
    server_url = f"http://localhost:{required('WEBHOOK_SERVER_PORT')}"
    serve(int(required("ADMIN_UI_PORT")), make_handler(listener_url, server_url))


if __name__ == "__main__":
    main()
