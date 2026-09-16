import re
import uuid

HEADER = "X-Correlation-ID"
VALID = re.compile(r"[A-Za-z0-9._-]{1,64}")


def correlation_id_from(value: str | None) -> str:
    return value if value and VALID.fullmatch(value) else str(uuid.uuid4())
