import os
from datetime import datetime, timezone


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"missing environment variable {name}")
    return value


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")
