#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VCR_PORT="${VCR_PORT:-7500}"
WEB_PORT="${WEB_PORT:-5173}"

for port in "$VCR_PORT" "$WEB_PORT"; do
  if lsof -ti tcp:"$port" >/dev/null 2>&1; then
    echo "ERROR: port $port is already in use, run scripts/stop.sh first"
    lsof -nP -iTCP:"$port" -sTCP:LISTEN | tail -n +2
    exit 1
  fi
done

mkdir -p .run logs

if [ ! -f cassettes/blog_list-posts.yaml ]; then
  .venv/bin/python backend/record.py
fi

if [ ! -d web/node_modules ]; then
  cd web && bun install && cd "$ROOT"
fi

wait_for() {
  local port="$1" name="$2" pid="$3" log="$4"
  for _ in $(seq 1 30); do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "ERROR: $name exited during startup"
      tail -20 "$log"
      exit 1
    fi
    if lsof -ti tcp:"$port" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "ERROR: $name never bound port $port"
  tail -20 "$log"
  exit 1
}

VCR_PORT="$VCR_PORT" "$ROOT/.venv/bin/python" "$ROOT/backend/server.py" > logs/player.log 2>&1 &
PLAYER_PID=$!
echo "$PLAYER_PID" > .run/player.pid

cd web
bun run dev -- --port "$WEB_PORT" --strictPort > "$ROOT/logs/web.log" 2>&1 &
WEB_PID=$!
echo "$WEB_PID" > "$ROOT/.run/web.pid"
cd "$ROOT"

wait_for "$VCR_PORT" player "$PLAYER_PID" logs/player.log
wait_for "$WEB_PORT" website "$WEB_PID" logs/web.log

echo "player  http://127.0.0.1:$VCR_PORT"
echo "website http://localhost:$WEB_PORT"
echo "logs    $ROOT/logs"
