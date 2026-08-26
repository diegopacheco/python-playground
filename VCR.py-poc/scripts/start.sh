#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VCR_PORT="${VCR_PORT:-7500}"
WEB_PORT="${WEB_PORT:-5173}"

mkdir -p .run logs

if [ ! -f cassettes/blog_list-posts.yaml ]; then
  .venv/bin/python backend/record.py
fi

if [ ! -d web/node_modules ]; then
  cd web && bun install && cd "$ROOT"
fi

VCR_PORT="$VCR_PORT" .venv/bin/python backend/server.py > logs/player.log 2>&1 &
echo $! > .run/player.pid

cd web
bun run dev --port "$WEB_PORT" > "$ROOT/logs/web.log" 2>&1 &
echo $! > "$ROOT/.run/web.pid"
cd "$ROOT"

for _ in $(seq 1 40); do
  if grep -q "vcr player on" logs/player.log 2>/dev/null && grep -q "Local:" logs/web.log 2>/dev/null; then
    break
  fi
  sleep 1
done

LOCAL="$(grep -o "http://localhost:[0-9]*" logs/web.log | head -1)"

echo "player  http://127.0.0.1:$VCR_PORT"
echo "website ${LOCAL:-http://127.0.0.1:$WEB_PORT}"
echo "logs    $ROOT/logs"
