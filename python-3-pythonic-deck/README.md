# python-3-pythonic-deck

A card deck implementing the Python sequence protocol, type checked by `pyright` in strict mode.

### What it does

`src/main.py` builds `Card` as a `NamedTuple` and `CardDeck` as a class that implements `__len__` and `__getitem__`, so the deck works with `len()`, indexing, slicing, iteration and `in`. `pyright` statically verifies every type.

### Stack

- Python 3.14.7
- pyright (strict)

### Architecture

`run.sh` -> runs `src/main.py` to show the program output -> runs `pyright`, which reads `pyrightconfig.json`, checks `src` in strict mode and prints the error count.

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
Card(rank='7', suit='diamonds')
0 errors, 0 warnings, 0 informations
```
