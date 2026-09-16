import json
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager

COLUMNS = ("id", "correlation_id", "type", "signature_valid", "relayed_at", "received_at", "headers", "payload")


class EventStore:
    def __init__(self, path: str) -> None:
        self.path = path
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS events ("
                "id TEXT PRIMARY KEY, correlation_id TEXT NOT NULL, type TEXT NOT NULL, signature_valid INTEGER NOT NULL, relayed_at TEXT, "
                "received_at TEXT NOT NULL, headers TEXT NOT NULL, payload TEXT NOT NULL)"
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self.path)) as connection, connection:
            yield connection

    def add(self, event: dict) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                f"INSERT OR IGNORE INTO events ({', '.join(COLUMNS)}) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event["id"],
                    event["correlation_id"],
                    event["type"],
                    int(event["signature_valid"]),
                    event["relayed_at"],
                    event["received_at"],
                    json.dumps(event["headers"]),
                    json.dumps(event["payload"]),
                ),
            )
            return cursor.rowcount == 1

    def all(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(f"SELECT {', '.join(COLUMNS)} FROM events ORDER BY rowid DESC").fetchall()
        return [
            {
                "id": row[0],
                "correlation_id": row[1],
                "type": row[2],
                "signature_valid": bool(row[3]),
                "relayed_at": row[4],
                "received_at": row[5],
                "headers": json.loads(row[6]),
                "payload": json.loads(row[7]),
            }
            for row in rows
        ]
