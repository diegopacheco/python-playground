# python-essentials-fire

Turn a plain Python class into a command line interface automatically with Google's `python-fire`.

### What it does

`src/main.py` defines a `Calculator` class and hands it to `fire.Fire`. Every method becomes a subcommand and its parameters become CLI arguments, with no argument parsing code written by hand.

### Features

- Zero-boilerplate CLI from a class
- Methods become subcommands (`add`, `sub`, `mul`, `div`)
- Positional and keyword arguments parsed automatically
- Built-in `--help` and interactive inspection

### Stack

- Python 3.14.6
- fire

### Architecture

`run.sh` -> `python3 src/main.py <method> <args>` -> `fire.Fire(Calculator)` inspects the class, maps the first argument to a method and the rest to its parameters -> the return value is printed.

### Usage

```bash
python3 src/main.py add 2 3
python3 src/main.py div 10 4
python3 src/main.py --help
```

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
add 2 3:
5
mul 4 5:
20
div 10 4:
2.5
```
