import os
from http.server import ThreadingHTTPServer

import api
import db


def main():
    port = int(os.getenv("API_PORT", "8080"))
    db.start()
    server = ThreadingHTTPServer(("0.0.0.0", port), api.Handler)
    print(f"listening on http://0.0.0.0:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        db.stop()


if __name__ == "__main__":
    main()
