#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

[ -x "$ROOT/.venv/bin/uvicorn" ] || fail "dependencies missing, run ./scripts/setup.sh first"

port="$(service_port backend)"
if port_up "$port"; then
  log "backend already up on $port"
else
  start_bg backend "$ROOT/src" "$ROOT/.venv/bin/uvicorn" --factory main:create_app --port "$port"
  wait_port_up "$port" 60 || fail "backend did not open port $port, see $LOGS/backend.log"
  log "backend up on $port"
fi

"$SCRIPTS/status.sh"
