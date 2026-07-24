# python-essentials-idiomatic

The Python way of doing things: comprehensions, `enumerate`/`zip`, unpacking and swapping, `dict.get`/`setdefault`, EAFP error handling, `str.join`, and ternary expressions.

### How it works

`src/main.py` groups each idiom into a function. Instead of manual index loops it uses comprehensions and `enumerate`; instead of checking keys first it uses `get`/`setdefault` and try/except (EAFP).

### Run

```bash
./run.sh
```

### Output

```
comprehensions: ([0, 1, 4, 9, 16, 25], {0, 2, 4, 6, 8}, {'a': 97, 'b': 98, 'c': 99})
enumerate_and_zip: ([('alice', 30), ('bob', 25)], [(1, 'alice'), (2, 'bob')])
unpacking: (1, [2, 3, 4], (20, 10))
dict_get_and_setdefault: ({'b': 1, 'a': 3, 'n': 2}, {'a': ['ant', 'ape'], 'b': ['bee']})
eafp: 42
string_join_and_ternary: ('python is fun', 'odd')
```
