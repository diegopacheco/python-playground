#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT/.run"
LOG_DIR="$RUN_DIR/logs"
PID_FILE="$RUN_DIR/game.pid"
PYTHON="$ROOT/.venv/bin/python"
export PYTHONPATH="$ROOT/src"
cd "$ROOT"

game_pid() {
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    cat "$PID_FILE"
  fi
}

require_venv() {
  if [ ! -x "$PYTHON" ]; then
    echo "missing .venv, run ./scripts/setup.sh first" >&2
    exit 1
  fi
}
