# python-essentials-jwt

JWT (HS256) built with only the standard library: `hmac`, `hashlib`, `base64`, `json`. No external dependency.

### How it works

`src/main.py` signs a payload into a `header.payload.signature` token, verifies the signature with `hmac.compare_digest`, and checks the `exp` claim. It then proves tampering and expiry are rejected.

### Run

```bash
./run.sh
```

### Output

```
token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZSIsInJvbGUiOiJhZG1pbiIsImV4cCI6...
verified payload: {'sub': 'alice', 'role': 'admin', 'exp': 1783887401}
tamper check: invalid signature
expiry check: token expired
```
