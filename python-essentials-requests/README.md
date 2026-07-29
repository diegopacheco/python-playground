# python-essentials-requests

The `requests` library: query params, JSON bodies, custom headers, status handling, and a reused `Session`.

### How it works

`src/main.py` calls `httpbin.org`: a `GET` with params, a `POST` with a JSON body, a request with custom headers, a 404 status check, and a `Session` that shares headers across calls. Needs network access.

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
get_with_params: {'lang': 'python', 'n': '3'}
post_json: {'name': 'alice', 'role': 'admin'}
custom_headers: abc123
status_handling: (404, False)
with_session: ('shared', 'shared')
```
