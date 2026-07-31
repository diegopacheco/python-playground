# python-essentials-slices

Slicing lists and strings: ranges, steps, negative indexes, reversing, slice assignment, and the `slice` object.

### How it works

`src/main.py` slices a list and a string with `[start:stop:step]`, mutates a list through slice assignment (including extended steps), and builds a reusable `slice` object.

### Run

```bash
./run.sh
```

### Output

```
basic_slices: {'first_three': [0, 1, 2], 'last_three': [7, 8, 9], 'middle': [3, 4, 5, 6], 'every_second': [0, 2, 4, 6, 8], 'reversed': [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]}
string_slices: {'prefix': 'python', 'suffix': 'playground', 'skip': 'ph-arn', 'reverse': 'dnuorgyalp-nohtyp'}
slice_assignment: ([1, 20, 30, 40, 4, 5], [0, 20, 0, 40, 0, 5])
slice_object: [0, 2, 4, 6, 8]
```
