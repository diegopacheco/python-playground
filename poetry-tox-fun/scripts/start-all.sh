#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

log "starting"

[ -x "$VENV/bin/notes-app" ] || fail "app is not installed, run ./scripts/setup.sh first"

port="$(service_port app)"
if port_up "$port"; then
  log "app already listening on $port"
else
  PORT="$port" start_bg app "$ROOT" "$VENV/bin/notes-app"
  wait_port_up "$port" 60 || fail "app did not open port $port, see $LOGS/app.log"
fi

"$SCRIPTS/status.sh"

log "links"
for name in $(service_names); do
  printf "%-14s %s\n" "$name" "$(service_url "$name")"
done
printf "%-14s %s\n" "api" "$(service_url app)/api/notes"
