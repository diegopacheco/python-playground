import re

RELAY_FIELDS = ("body", "query", "timestamp")
PRIVATE_NAME = re.compile(r"ip|forwarded|url|port|origin|referer", re.IGNORECASE)
PRIVATE_VALUE = re.compile(r"\d{1,3}(\.\d{1,3}){3}|[0-9a-f]{0,4}(:[0-9a-f]{0,4}){2,}|smee\.io/", re.IGNORECASE)


def is_private(name: str, value: object) -> bool:
    return bool(PRIVATE_NAME.search(name) or PRIVATE_VALUE.search(str(value)))


def received_headers(message: dict) -> dict:
    return {
        name: "[redacted]" if is_private(name, value) else value
        for name, value in message.items()
        if name not in RELAY_FIELDS
    }
