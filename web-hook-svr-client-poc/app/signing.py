import hashlib
import hmac
import json


def canonical(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def sign(secret: str, timestamp: str, payload: dict) -> str:
    message = f"{timestamp}.{canonical(payload)}".encode()
    return "sha256=" + hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def verify(secret: str, timestamp: str | None, payload: dict, signature: str | None) -> bool:
    if not timestamp or not signature:
        return False
    return hmac.compare_digest(sign(secret, timestamp, payload), signature)
