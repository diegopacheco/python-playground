# python-essentials-semaphores

Semaphores for limiting concurrency: `Semaphore` capping parallel workers, `BoundedSemaphore` guarding against over-release, and a semaphore acting as a connection pool.

### How it works

`src/main.py` starts 8 threads but a `Semaphore(2)` keeps the peak concurrency at 2, a `BoundedSemaphore` raises on an extra `release`, and a `Semaphore(3)` limits how many clients hold a slot at once.

### Run

```bash
./run.sh
```

### Output

```
limit_concurrency peak (max 2): 2
bounded_semaphore_guard: over-release blocked
connection_pool served: [0, 1, 2, 3, 4, 5]
```
