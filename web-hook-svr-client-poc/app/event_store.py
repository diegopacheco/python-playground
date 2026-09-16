import json
import sqlite3


class EventStore:
    def __init__(self, path: str):
        self.path = path
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS events ("
                "id TEXT PRIMARY KEY, type TEXT NOT NULL, signature_valid INTEGER NOT NULL, "
                "received_at TEXT NOT NULL, payload TEXT NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def add(self, event: dict) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO events VALUES (?, ?, ?, ?, ?)",
                (event["id"], event["type"], int(event["signature_valid"]), event["received_at"], json.dumps(event["payload"])),
            )
            return cursor.rowcount == 1

    def all(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, type, signature_valid, received_at, payload FROM events ORDER BY rowid DESC"
            ).fetchall()
        return [
            {"id": row[0], "type": row[1], "signature_valid": bool(row[2]), "received_at": row[3], "payload": json.loads(row[4])}
            for row in rows
        ]
