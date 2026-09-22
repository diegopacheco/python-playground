#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

log "starting"
require uv
[ -f "$ROOT/models/router.onnx" ] || fail "models/router.onnx missing, run ./scripts/setup.sh first"

port="$(service_port router)"
start_bg router "$ROOT" env PORT="$port" uv run onnx-router
wait_port_up "$port" 60 || fail "router did not open port $port, see $LOGS/router.log"
log "router up on $(service_url router)"

"$SCRIPTS/status.sh"

log "links"
for name in $(service_names); do
  printf "%-14s %s\n" "$name" "$(service_url "$name")"
done
printf "%-14s %s\n" "api" "$(service_url router)/api/route"
