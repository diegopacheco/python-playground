import urllib.error
import urllib.request
from pathlib import Path

from app.config import required
from app.http_json import JsonHandler, serve

INDEX = Path(__file__).parent / "static" / "index.html"
PROXIED = ("/api/events", "/health")


def make_handler(listener_url: str) -> type[JsonHandler]:
    class Handler(JsonHandler):
        def do_GET(self):
            if self.path in ("/", "/index.html"):
                return self.send_bytes(200, INDEX.read_bytes(), "text/html; charset=utf-8")
            if self.path in PROXIED:
                return self.proxy()
            self.send_json(404, {"error": "not found"})

        def proxy(self):
            try:
                with urllib.request.urlopen(listener_url + self.path, timeout=5) as response:
                    self.send_bytes(response.status, response.read(), "application/json")
            except (urllib.error.URLError, TimeoutError) as error:
                self.send_json(502, {"error": f"listener unavailable: {error}"})

    return Handler


def main():
    listener_url = f"http://localhost:{required('LISTENER_PORT')}"
    serve(int(required("ADMIN_UI_PORT")), make_handler(listener_url))


if __name__ == "__main__":
    main()
