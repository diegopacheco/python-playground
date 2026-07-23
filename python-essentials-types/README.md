# python-essentials-types

Strong typing with the `typing` module: type hints, `TypedDict`, `NewType`, `Protocol`, and a `Generic` class.

### How it works

`src/main.py` annotates every function, defines a `Stack[T]` generic, a `User` TypedDict, a `UserId` NewType, and a `Comparable` Protocol used for structural typing. Check it statically with `mypy src/main.py`.

### Run

```bash
./run.sh
```

### Output

```
greet: hi alice hi alice
stack pop: 2 size: 1
find_user: {'id': 2, 'name': 'bob', 'email': 'b@x.com'}
total_prices: 4.0
smallest: 1
```
