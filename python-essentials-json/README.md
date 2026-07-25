# python-essentials-json

JSON support with the standard library `json` module: `dumps`/`loads`, pretty printing, a custom encoder, and type mapping.

### How it works

`src/main.py` serializes and parses a dict, pretty prints with `indent` and `sort_keys`, serializes a `datetime` via a custom `JSONEncoder`, and shows how JSON types map to Python types.

### Run

```bash
./run.sh
```

### Output

```
dumps: {"name": "alice", "age": 30, "roles": ["admin", "user"], "active": true}
loads: {'name': 'alice', 'age': 30, 'roles': ['admin', 'user'], 'active': True}
pretty_print:
{
  "a": 1,
  "b": 2,
  "nested": {
    "x": 10,
    "y": 20
  }
}
custom_encoder: {"name": "login", "at": "2026-07-12T09:30:00"}
parse_numbers: ('int', 'float', [1, 2, 3])
```
