# python-essentials-basics

Python building blocks: `for`, `while`, looping over collections, `lambda`, `sorted` with keys, and classes with inheritance.

### How it works

`src/main.py` has one function per concept. `for_loop` sums a range, `while_loop` halves a number counting steps, `loop_over_collection` uses `enumerate`, `lambdas` builds anonymous functions, `sorting` sorts tuples by different keys, and `Animal`/`Dog` show a class with a subclass.

### Run

```bash
./run.sh
```

### Output

```
for_loop sum 1..5: 15
while_loop halving steps: 3
loop_over_collection: ['0:apple', '1:banana', '2:cherry']
lambdas: (25, 7)
sorted by age: [('bob', 25), ('alice', 30), ('carol', 35)]
sorted by name desc: [('carol', 35), ('bob', 25), ('alice', 30)]
class describe: Rex has 4 legs
class method: woof
isinstance Animal: True
```
