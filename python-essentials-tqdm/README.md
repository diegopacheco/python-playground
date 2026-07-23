# python-essentials-tqdm

Smart progress bars for loops and iterables with `tqdm`.

### What it does

`src/main.py` wraps a `range` and a list in `tqdm`, which draws a live progress bar showing percentage, count, elapsed and remaining time, and iterations per second while the loop runs.

### Features

- Progress bar over any iterable
- Custom description labels (`desc`)
- Live rate, ETA, and elapsed time
- Zero changes to the loop body

### Stack

- Python 3.14.6
- tqdm

### Architecture

`run.sh` -> `src/main.py` wraps each iterable in `tqdm(...)` -> on every iteration tqdm updates its counters and repaints the bar on stderr.

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
processing: 100%|██████████████████████████| 50/50 [00:01<00:00, 49.5it/s]
total: 1225
letters: 100%|██████████████████████████████| 4/4 [00:00<00:00,  9.9it/s]
```
