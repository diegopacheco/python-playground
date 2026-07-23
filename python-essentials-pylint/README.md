# python-essentials-pylint

Fully type-annotated Python linted by `pylint` to a clean 10.00/10 score.

### What it does

`src/main.py` models a small banking flow (`Account`, `transfer`, `total_balance`) where every function and method is type annotated. `pylint` statically checks it for errors, style, and conventions.

### Features

- Type annotations on every function, method, and return value
- `dataclass` with typed fields
- `list[Account]` generic annotation
- `.pylintrc` tuned to keep the code comment and docstring free
- `run.sh` executes the program then lints it

### Stack

- Python 3.14.6
- pylint

### Architecture

`run.sh` -> runs `src/main.py` to show the program output -> runs `pylint src/main.py` which parses the AST, evaluates its checkers, and prints a score.

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
alice balance: 70.0
bob balance: 80.0
total balance: 150.0

--------------------------------------------------------------------
Your code has been rated at 10.00/10
```
