import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_key():
    return AESGCM.generate_key(bit_length=256)


def encrypt(key, plaintext):
    nonce = os.urandom(12)
    cipher = AESGCM(key)
    ciphertext = cipher.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()


def decrypt(key, token):
    raw = base64.b64decode(token)
    nonce, ciphertext = raw[:12], raw[12:]
    cipher = AESGCM(key)
    return cipher.decrypt(nonce, ciphertext, None).decode()


def main():
    key = generate_key()

    records = {
        "name": "Alice Johnson",
        "ssn": "123-45-6789",
        "email": "alice@example.com",
        "phone": "+1-555-0100",
    }

    encrypted = {field: encrypt(key, value) for field, value in records.items()}
    for field, token in encrypted.items():
        print(f"encrypted {field}: {token}")

    print("---")

    decrypted = {field: decrypt(key, token) for field, token in encrypted.items()}
    for field, value in decrypted.items():
        print(f"decrypted {field}: {value}")

    print("---")
    print("roundtrip ok:", decrypted == records)

    tampered = encrypted["ssn"][:-2] + ("AA" if not encrypted["ssn"].endswith("AA") else "BB")
    try:
        decrypt(key, tampered)
    except Exception:
        print("tamper detected: authentication failed")


if __name__ == "__main__":
    main()
