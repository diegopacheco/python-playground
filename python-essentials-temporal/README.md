# python-essentials-temporal

A Temporal workflow with two activities, run against a local Temporal server (in podman) using the `temporalio` SDK on Python 3.14.6.

### How it works

`src/main.py` defines the `greet` and `shout` activities and a `GreetingWorkflow` that chains them. It connects to `localhost:7233`, starts a worker on a task queue, and executes the workflow.

The Temporal server runs in podman via `docker-compose.yml` using the `temporalio/temporal` image with `server start-dev`.

### Install

```bash
./install-deps.sh
```

### Start Temporal

```bash
./start.sh
```

UI is available at http://localhost:8233

### Run

```bash
./run.sh
```

### Stop Temporal

```bash
./stop.sh
```

### Test

Starts Temporal, runs the workflow, then stops Temporal:

```bash
./test.sh
```

### Output

```
workflow result: HELLO ALICE
```
