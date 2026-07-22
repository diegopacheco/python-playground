# python-essentials-hidden-gems

Lesser-known Python features: `for/else`, the walrus operator `:=`, dict merge `|`, f-string `=` debugging, and `collections`/`itertools` helpers.

### How it works

`src/main.py` shows a loop `else` that runs when no `break` fires, filtering with an assignment expression, merging dicts with `|`, self-documenting f-strings, and tools like `Counter`, `defaultdict`, `namedtuple`, `chain`, `accumulate`, `groupby`.

### Run

```bash
./run.sh
```

### Output

```
for_else: no even number found
walrus: [16, 25, 36]
dict_merge: {'color': 'black', 'size': 'l', 'material': 'cotton'}
fstring_debug: width=4 height=5 width * height=20
collections_tools: ([('i', 4), ('s', 4)], {3: ['ant', 'cat', 'bee'], 4: ['bear']}, (3, 4))
itertools_tools: ([1, 2, 3, 4, 5], [1, 3, 6, 10], {'a': ['a'], 'b': ['b', 'b', 'b'], 'c': ['c', 'c']})
```
