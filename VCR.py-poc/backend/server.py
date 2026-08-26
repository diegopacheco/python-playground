import json
import mimetypes
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import api
import tapes

PORT = int(os.environ.get("VCR_PORT", "7500"))

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Expose-Headers": "X-Vcr-Cassette, X-Vcr-Played, X-Vcr-Retaped",
}


class Player(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        sys.stderr.write("player %s\n" % (fmt % args))

    def send_bytes(self, status, blob, content_type, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(blob)))
        for key, value in list(CORS.items()) + list((extra or {}).items()):
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(blob)

    def send_json(self, status, payload, extra=None):
        self.send_bytes(status, json.dumps(payload).encode("utf-8"), "application/json", extra)

    def do_OPTIONS(self):
        self.send_bytes(204, b"", "text/plain")

    def read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def serve_image_bytes(self, image_id):
        path = os.path.join(api.IMAGE_DIR, image_id)
        if not os.path.exists(path):
            return self.send_json(404, {"error": "image bytes not on disk", "id": image_id})
        with open(path, "rb") as handle:
            blob = handle.read()
        self.send_bytes(200, blob, mimetypes.guess_type(image_id)[0] or "image/png", {"Cache-Control": "no-store"})

    def replay(self, method, path, query=""):
        response, meta = tapes.play(method, path, query)
        headers = {"X-Vcr-Cassette": meta["cassette"], "X-Vcr-Played": str(meta["played"])}
        self.send_bytes(response.status_code, response.content, "application/json", headers)

    def handle_write(self, path, body):
        handler = api.WRITES[path]
        payload, updates = handler(body)
        retaped = [tapes.write("GET", target, value) for target, value in updates.items()]
        for prefix, stale in api.STALE_ON_WRITE.items():
            if path.startswith(prefix):
                retaped += ["-" + name for name in tapes.eject(stale)]
        tapes.write("POST", path, payload, status=200)
        response, meta = tapes.play("POST", path)
        headers = {"X-Vcr-Cassette": meta["cassette"], "X-Vcr-Played": str(meta["played"]), "X-Vcr-Retaped": ",".join(retaped)}
        self.send_bytes(response.status_code, response.content, "application/json", headers)

    def route(self):
        path, _, query = self.path.partition("?")
        if path.startswith("/images/raw/"):
            return self.serve_image_bytes(path.rsplit("/", 1)[-1])
        if path == "/tapes/list-tapes":
            items = tapes.catalog()
            tapes.write("GET", path, {"items": items, "total": len(items), "dir": tapes.CASSETTE_DIR})
            return self.replay("GET", path)
        try:
            if path in api.WRITES:
                return self.handle_write(path, self.read_body())
            if path in api.READS:
                payload = api.READS[path](parse_qs(query).get("q", [""])[0])
                tapes.write("GET", path, payload, query=query)
                return self.replay("GET", path, query)
            return self.replay(self.command, path, query)
        except tapes.NoTape:
            return self.send_json(501, {"error": "no cassette for this endpoint", "endpoint": path, "hint": "run scripts/record.sh to lay down the tapes"})
        except LookupError as error:
            return self.send_json(404, {"error": str(error)})
        except ValueError as error:
            return self.send_json(400, {"error": str(error)})

    do_GET = do_POST = route


def main():
    if not tapes.exists("/blog/list-posts"):
        api.seed()
    os.makedirs(api.IMAGE_DIR, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Player)
    sys.stderr.write("vcr player on http://127.0.0.1:%d\ntapes %s\nimages %s\n" % (PORT, tapes.CASSETTE_DIR, api.IMAGE_DIR))
    server.serve_forever()


if __name__ == "__main__":
    main()
