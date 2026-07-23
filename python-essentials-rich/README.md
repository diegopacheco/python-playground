# python-essentials-rich

Rich terminal output with `rich`: panels, colored tables, inline markup, and rules.

### What it does

`src/main.py` prints a bordered panel, a styled multi-column table of books, an inline-markup status line, and a horizontal rule, all rendered by `rich` with color and box drawing.

### Features

- `Panel` with a title and border
- `Table` with per-column styles and alignment
- Inline console markup (`[bold red]...[/]`)
- Horizontal `rule`

### Stack

- Python 3.14.6
- rich

### Architecture

`run.sh` -> `src/main.py` builds `Panel` and `Table` renderables -> `Console.print` measures the terminal, applies styles, and emits ANSI escape codes.

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
╭────────────────── rich ──────────────────╮
│ Rich makes terminals beautiful            │
╰───────────────────────────────────────────╯
                    Books
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━┓
┃ Title                    ┃ Author        ┃ Year ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━┩
│ Clean Code               │ Robert Martin │ 2008 │
│ Refactoring              │ Martin Fowler │ 1999 │
│ The Pragmatic Programmer │ Andy Hunt     │ 1999 │
└──────────────────────────┴───────────────┴──────┘
error success warning
───────────────────── done ─────────────────────
```
