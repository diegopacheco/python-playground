# python-essentials-pydantic

Data validation and parsing with Pydantic v2: typed models, field constraints, custom validators, nested models, and structured error reporting.

### What it does

`src/main.py` defines a nested `User` and `Address` model with field constraints and a custom email validator. It builds a valid instance, serializes it to a dict and JSON, then triggers a `ValidationError` on bad input and prints each error.

### Features

- Typed `BaseModel` classes
- Field constraints (`min_length`, `ge`, `le`, regex `pattern`)
- Custom `field_validator`
- Nested model validation
- `model_dump` / `model_dump_json` serialization
- Structured `ValidationError` with per-field messages

### Stack

- Python 3.14.6
- pydantic v2

### Architecture

`run.sh` -> `src/main.py` constructs `User` -> pydantic coerces and validates each field, recursing into `Address` -> valid data is dumped to dict/JSON; invalid data raises `ValidationError` whose `.errors()` are iterated and printed.

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
valid user: {'id': 1, 'name': 'alice', 'age': 30, 'email': 'alice@example.com', 'address': {'street': '1 Main St', 'city': 'Lisbon', 'zipcode': '10001'}}
json: {"id":1,"name":"alice","age":30,"email":"alice@example.com","address":{"street":"1 Main St","city":"Lisbon","zipcode":"10001"}}
error count: 4
  ('name',): String should have at least 1 character
  ('age',): Input should be less than or equal to 130
  ('email',): Value error, invalid email
  ('address', 'zipcode'): String should match pattern '^\d{5}$'
```
