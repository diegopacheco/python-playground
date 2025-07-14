### Intall dependencies

```bash
./install-deps.sh
```

### Run

```bash
./run.sh
```

### Result

```
❯ ./run.sh
Person(name='Alice', age=30)
``` 

### About Data Classes

The @dataclass decorator added in Python 3.7 that automatically generates several special methods for your class.

What @dataclass generates automatically:
* __init__ method - Constructor that takes the class fields as parameters
* __repr__ method - String representation for debugging
* __eq__ method - Equality comparison between instances