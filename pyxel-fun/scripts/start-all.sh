#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require_venv
pid="$(game_pid)"
if [ -n "$pid" ]; then
  echo "game already running, pid $pid"
  exit 0
fi
mkdir -p "$LOG_DIR"
nohup "$PYTHON" "$ROOT/src/main.py" >"$LOG_DIR/game.log" 2>&1 &
echo $! >"$PID_FILE"
for _ in 1 2 3; do
  sleep 1
  if [ -z "$(game_pid)" ]; then
    rm -f "$PID_FILE"
    echo "game failed to start, see .run/logs/game.log" >&2
    exit 1
  fi
done
echo "game running in its own window, pid $(cat "$PID_FILE")"
