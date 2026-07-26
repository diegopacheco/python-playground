import base64
import hashlib
import hmac
import json
import time


def b64url_encode(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def b64url_decode(text):
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def sign(payload, secret):
    header = {"alg": "HS256", "typ": "JWT"}
    header_part = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_part = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_part}.{payload_part}".encode()
    signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    return f"{header_part}.{payload_part}.{b64url_encode(signature)}"


def verify(token, secret):
    header_part, payload_part, signature_part = token.split(".")
    signing_input = f"{header_part}.{payload_part}".encode()
    expected = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, b64url_decode(signature_part)):
        raise ValueError("invalid signature")
    payload = json.loads(b64url_decode(payload_part))
    if "exp" in payload and payload["exp"] < time.time():
        raise ValueError("token expired")
    return payload


def main():
    secret = "super-secret-key"
    payload = {"sub": "alice", "role": "admin", "exp": int(time.time()) + 3600}

    token = sign(payload, secret)
    print("token:", token)

    verified = verify(token, secret)
    print("verified payload:", verified)

    try:
        verify(token, "wrong-secret")
    except ValueError as error:
        print("tamper check:", error)

    expired = sign({"sub": "bob", "exp": int(time.time()) - 10}, secret)
    try:
        verify(expired, secret)
    except ValueError as error:
        print("expiry check:", error)


if __name__ == "__main__":
    main()
