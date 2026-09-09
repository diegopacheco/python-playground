#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

BACKEND_PORT="$(service_port backend)"
FRONTEND_PORT="$(service_port frontend)"

[ -x "$ROOT/.venv/bin/python" ] || fail "missing venv, run scripts/setup.sh first"
[ -d "$ROOT/frontend/node_modules" ] || fail "missing frontend deps, run scripts/setup.sh first"

export API_PORT="$BACKEND_PORT"
export API_URL="http://127.0.0.1:$BACKEND_PORT"

start_bg backend "$ROOT" "$ROOT/.venv/bin/python" src/main.py
wait_port_up "$BACKEND_PORT" 60 || fail "backend did not come up on $BACKEND_PORT, see .run/logs/backend.log"
log "backend up on $BACKEND_PORT"

start_bg frontend "$ROOT/frontend" bun run dev --port "$FRONTEND_PORT" --strictPort
wait_port_up "$FRONTEND_PORT" 60 || fail "frontend did not come up on $FRONTEND_PORT, see .run/logs/frontend.log"
log "frontend up on $FRONTEND_PORT"

log "open http://localhost:$FRONTEND_PORT"
