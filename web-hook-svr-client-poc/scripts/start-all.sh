#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

load_relay
export_ports
export LISTENER_DB="$DATA/listener.db"

log "starting"

if ! port_up "$LISTENER_PORT"; then
  rm -f "$LISTENER_DB"
  log "listener data cleared, the admin UI starts empty"
fi

start_bg listener python3 -m app.listener
wait_port_up "$LISTENER_PORT" 60 || fail "listener did not open port $LISTENER_PORT, see .run/logs/listener.log"
wait_listener_connected || fail "listener could not connect to the public relay, see .run/logs/listener.log"
log "listener up and connected to the public relay"

start_bg webhook_server python3 -m app.webhook_server
wait_port_up "$WEBHOOK_SERVER_PORT" 60 || fail "webhook_server did not open port $WEBHOOK_SERVER_PORT, see .run/logs/webhook_server.log"

start_bg admin_ui python3 -m app.admin_ui
wait_port_up "$ADMIN_UI_PORT" 60 || fail "admin_ui did not open port $ADMIN_UI_PORT, see .run/logs/admin_ui.log"

"$SCRIPTS/status.sh"

log "links"
for name in $(service_names); do
  printf "%-16s %s\n" "$name" "$(service_url "$name")"
done
