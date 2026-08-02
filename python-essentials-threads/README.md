# python-essentials-threads

Threads every way: raw `Thread`, `Lock` for shared state, `ThreadPoolExecutor`, returning results through a `Queue`, and daemon threads.

### How it works

`src/main.py` runs one function per style. `thread_with_lock` proves a lock stops races (4 threads × 10000 increments == 40000), the pool fans out slow work, the queue collects results, and a daemon thread runs in the background until the process exits.

### Run

```bash
./run.sh
```

### Output

```
basic_thread: [0, 1, 4, 9, 16]
thread_with_lock: 40000
thread_pool: [0, 1, 4, 9, 16, 25, 36, 49]
result_via_queue: [0, 10, 20, 30, 40]
daemon_thread ran: True
```
