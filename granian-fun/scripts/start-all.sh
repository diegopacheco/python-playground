#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require_venv
log "starting"

port="$(service_port backend)"
start_bg backend "$ROOT/src" "$VENV/bin/granian" --interface rsgi --host 127.0.0.1 --port "$port" --workers 1 main:app
wait_port_up "$port" 60 || fail "backend did not open port $port, see $LOGS/backend.log"
log "backend up on $(service_url backend)"

"$SCRIPTS/status.sh"

log "links"
for name in $(service_names); do
  printf "%-14s %s\n" "$name" "$(service_url "$name")"
done
printf "%-14s %s\n" "health" "$(service_url backend)/health"
printf "%-14s %s\n" "tasks" "$(service_url backend)/tasks"
