#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

for name in player web; do
  FILE=".run/$name.pid"
  if [ -f "$FILE" ]; then
    PID="$(cat "$FILE")"
    if kill -0 "$PID" 2>/dev/null; then
      pkill -P "$PID" 2>/dev/null || true
      kill "$PID" 2>/dev/null || true
      echo "stopped $name ($PID)"
    fi
    rm -f "$FILE"
  fi
done

lsof -ti tcp:"${VCR_PORT:-7500}" | xargs kill 2>/dev/null || true
lsof -ti tcp:"${WEB_PORT:-5173}" | xargs kill 2>/dev/null || true
echo "stop done"
