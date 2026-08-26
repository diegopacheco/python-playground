#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VCR_PORT="${VCR_PORT:-7500}"
WEB_PORT="${WEB_PORT:-5173}"

free_port() {
  local port="$1"
  local pids
  pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
  [ -z "$pids" ] && return 0
  echo "$pids" | xargs kill 2>/dev/null || true
  for _ in $(seq 1 10); do
    pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
    [ -z "$pids" ] && return 0
    sleep 1
  done
  pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
  [ -n "$pids" ] && echo "$pids" | xargs kill -9 2>/dev/null || true
  return 0
}

for name in player web; do
  FILE=".run/$name.pid"
  if [ -f "$FILE" ]; then
    PID="$(cat "$FILE")"
    pkill -P "$PID" 2>/dev/null || true
    kill "$PID" 2>/dev/null || true
    rm -f "$FILE"
  fi
done

pkill -f "$ROOT/backend/server.py" 2>/dev/null || true
pkill -f "$ROOT/web/node_modules/.bin/vite" 2>/dev/null || true

free_port "$VCR_PORT"
free_port "$WEB_PORT"

LEFT=""
for port in "$VCR_PORT" "$WEB_PORT"; do
  if lsof -ti tcp:"$port" >/dev/null 2>&1; then
    LEFT="$LEFT $port"
  fi
done

if [ -n "$LEFT" ]; then
  echo "ERROR: still bound after stop:$LEFT"
  for port in $LEFT; do lsof -nP -iTCP:"$port" -sTCP:LISTEN | tail -n +2; done
  exit 1
fi

echo "stopped, ports $VCR_PORT and $WEB_PORT are free"
