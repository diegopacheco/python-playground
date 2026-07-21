# python-essentials-functional

Functional programming in Python: `map`, `filter`, `reduce`, closures, `functools.partial`, and function composition.

### How it works

`src/main.py` transforms a list with `map`/`filter`/`reduce`, builds closures that capture state (`make_counter`, `multiplier`), fixes arguments with `partial`, and composes functions into a pipeline.

### Run

```bash
./run.sh
```

### Output

```
map_filter_reduce: ([2, 4, 6, 8, 10, 12], [2, 4, 6], 21)
closure counter: 1 2 3
closure multiplier: 30
partials: (25, 8)
compose (x*2)+1 of 5: 11
```
