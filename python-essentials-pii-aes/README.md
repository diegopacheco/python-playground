# python-essentials-pii-aes

Encrypt and decrypt PII with AES-256-GCM using the `cryptography` library. GCM gives confidentiality plus tamper detection.

### How it works

`src/main.py` generates a 256-bit key, encrypts each PII field with a fresh random 12-byte nonce, base64-encodes `nonce + ciphertext`, then decrypts back. Because GCM is authenticated, a modified ciphertext fails to decrypt.

### Install

```bash
./install-deps.sh
```

### Run

```bash
./run.sh
```

### Output

```
encrypted name: FwfwL44m2eYzXthyY1gtYwHcyug1x6dX5Egxwrl2WFL0H7KcC93Z/b0=
encrypted ssn: 0GWjISjXit9Vk3RXTucfK+xT1doVqnzO/bc1K689t24yl25w3D1g
...
decrypted name: Alice Johnson
decrypted ssn: 123-45-6789
...
roundtrip ok: True
tamper detected: authentication failed
```
