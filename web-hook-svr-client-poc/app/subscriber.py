import json
import threading
import urllib.error
import urllib.request
import uuid
from collections.abc import Iterable, Iterator
from datetime import datetime, timezone

from app.config import now_iso
from app.event_store import EventStore
from app.private_headers import received_headers
from app.signing import verify

WEBHOOK_HEADERS = ("x-webhook-event", "x-webhook-timestamp", "x-webhook-signature")


def parse_sse(lines: Iterable[bytes]) -> Iterator[tuple[str, str]]:
    event, data = "message", []
    for raw in lines:
        line = raw.decode().rstrip("\r\n")
        if line == "":
            if data:
                yield event, "\n".join(data)
            event, data = "message", []
        elif line.startswith("event:"):
            event = line[len("event:"):].strip()
        elif line.startswith("data:"):
            data.append(line[len("data:"):].lstrip())


def to_event(message: dict, secret: str) -> dict | None:
    body = message.get("body")
    if not isinstance(body, dict):
        return None
    webhook = {name: message.get(name) for name in WEBHOOK_HEADERS}
    return {
        "id": str(body.get("id") or uuid.uuid4()),
        "type": str(webhook["x-webhook-event"] or "unknown"),
        "signature_valid": verify(secret, webhook["x-webhook-timestamp"], body, webhook["x-webhook-signature"]),
        "relayed_at": relayed_at(message.get("timestamp")),
        "received_at": now_iso(),
        "headers": received_headers(message),
        "payload": body,
    }


def relayed_at(timestamp: object) -> str | None:
    if not isinstance(timestamp, (int, float)):
        return None
    return datetime.fromtimestamp(timestamp / 1000, timezone.utc).isoformat(timespec="milliseconds")


class RelaySubscriber:
    def __init__(self, relay_url: str, secret: str, store: EventStore) -> None:
        self.relay_url = relay_url
        self.secret = secret
        self.store = store
        self.connected = threading.Event()

    def consume(self, lines: Iterable[bytes]) -> None:
        for event, data in parse_sse(lines):
            if event == "ready":
                self.connected.set()
                print("relay connected", flush=True)
            elif event == "message":
                record = to_event(json.loads(data), self.secret)
                if record and self.store.add(record):
                    print(f"received {record['type']} valid={record['signature_valid']}", flush=True)

    def run_forever(self) -> None:
        request = urllib.request.Request(self.relay_url, headers={"Accept": "text/event-stream"})
        while True:
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    self.consume(response)
            except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
                print(f"relay disconnected: {type(error).__name__}", flush=True)
            self.connected.clear()
            threading.Event().wait(2)

    def start(self) -> None:
        threading.Thread(target=self.run_forever, daemon=True).start()
