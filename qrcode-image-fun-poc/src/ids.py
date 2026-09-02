import base64
import hashlib
import hmac
import os

from store import DATA

SECRET = DATA / "secret.bin"
NONCE_BYTES = 12
MAC_BYTES = 10


def _secret() -> bytes:
    if not SECRET.exists():
        SECRET.write_bytes(os.urandom(32))
        SECRET.chmod(0o600)
    return SECRET.read_bytes()


def _b32(raw: bytes) -> str:
    return base64.b32encode(raw).decode().rstrip("=")


def _unb32(text: str) -> bytes:
    pad = "=" * (-len(text) % 8)
    return base64.b32decode(text + pad)


def _tag(nonce: bytes) -> bytes:
    return hmac.new(_secret(), nonce, hashlib.sha256).digest()[:MAC_BYTES]


def mint() -> str:
    nonce = os.urandom(NONCE_BYTES)
    return _b32(nonce) + _b32(_tag(nonce))


def verify(page_id: str) -> bool:
    split = len(_b32(b"\0" * NONCE_BYTES))
    if len(page_id) != split + len(_b32(b"\0" * MAC_BYTES)):
        return False
    try:
        nonce = _unb32(page_id[:split])
        tag = _unb32(page_id[split:])
    except Exception:
        return False
    return hmac.compare_digest(_tag(nonce), tag)
