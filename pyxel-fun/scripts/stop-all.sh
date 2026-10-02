#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

pid="$(game_pid)"
if [ -z "$pid" ]; then
  rm -f "$PID_FILE"
  echo "game not running"
  exit 0
fi
kill "$pid"
for _ in $(seq 1 10); do
  if ! kill -0 "$pid" 2>/dev/null; then
    rm -f "$PID_FILE"
    echo "game stopped, pid $pid"
    exit 0
  fi
  sleep 1
done
echo "game pid $pid did not stop" >&2
exit 1
