# python-essentials-pyproject

A packaged Python project defined entirely by `pyproject.toml`, installable with `pip install -e .` and exposing a console script.

### What it does

Declares a `greeter` package under a `src/` layout with a PEP 621 `[project]` table, a setuptools build backend, and a `[project.scripts]` entry point that installs a `greeter` command on the PATH.

### Features

- PEP 621 metadata in `pyproject.toml`
- setuptools build backend
- `src/` layout with package discovery
- Console script entry point (`greeter`)
- Editable install with `pip install -e .`

### Stack

- Python 3.14.6
- setuptools (pyproject.toml)

### Architecture

`pyproject.toml` -> setuptools reads `[project]` metadata and finds packages under `src/` -> `pip install -e .` installs the package editable and creates the `greeter` console script -> `run.sh` calls `greeter Diego` which dispatches to `greeter.cli:main`.

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
hello Diego
```
