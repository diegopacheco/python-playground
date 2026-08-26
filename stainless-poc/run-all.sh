#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if ! .venv/bin/python -c "import taskly" >/dev/null 2>&1; then
  echo "the taskly sdk is not installed, run ./generate-sdk.sh first"
  exit 1
fi

.venv/bin/python server/main.py &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT

READY=0
for _ in $(seq 1 30); do
  if .venv/bin/python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${TASKLY_PORT:-8080}/status')" >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 1
done

if [ "$READY" -ne 1 ]; then
  echo "taskly server did not start"
  exit 1
fi

.venv/bin/python client/main.py
