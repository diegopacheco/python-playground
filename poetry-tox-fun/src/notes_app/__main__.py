import os

from notes_app.server import NotesServer
from notes_app.store import NoteStore


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8080"))
    with NotesServer((host, port), NoteStore()) as server:
        print(f"notes app on http://{host}:{port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
