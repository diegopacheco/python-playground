# python-uv-worksteal

POC of pytest-xdist `--dist worksteal` running under uv, type checked with ty, with proof that work stealing really happens.

## Stack

* uv 0.10 + Python 3.14.7
* pytest 9 + pytest-xdist 3.8 (`--dist worksteal`)
* ty + ruff

## How the proof works

`src/worksteal/plugin.py` uses the public xdist hook `pytest_xdist_make_scheduler` to swap in a subclass of `WorkStealingScheduling`.
Every time a busy worker hands back queued tests after a steal request, the subclass records the victim worker and the stolen test ids.
The plugin also records which worker actually ran each test.
A test that was queued on `gw0` and ran on `gw1` is hard evidence that it was stolen.

`workload/test_workload.py` is intentionally skewed: 8 slow tests (0.5s) followed by 8 fast tests (0.01s).
worksteal splits the queue in half, so one worker gets all slow tests and the other gets all fast tests.
The fast worker goes idle and steals half of the slow queue.

## Run

```bash
uv sync
./scripts/prove.sh
./scripts/test-all.sh
```

`prove.sh` output:

```
============================ work stealing evidence ============================
workload/test_workload.py::test_job[slow-4]  queued on gw0  stolen and run by gw1
workload/test_workload.py::test_job[slow-5]  queued on gw0  stolen and run by gw1
workload/test_workload.py::test_job[slow-6]  queued on gw0  stolen and run by gw1
workload/test_workload.py::test_job[slow-7]  queued on gw0  stolen and run by gw1
steal events: 1
============================== 16 passed in 2.32s ==============================
stolen tests: 4  ran on another worker: 4
```

`test-all.sh` runs ruff, `ty check` and `uv run pytest -n 2 --dist worksteal`.
`tests/test_worksteal.py` runs the workload in a subprocess and fails if no test was stolen, if a stolen test ran on its original worker, or if a stolen test was not one of the slow ones stuck in the queue.
Switching the inner run to `--dist load` makes it fail.
