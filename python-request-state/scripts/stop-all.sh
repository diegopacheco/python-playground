#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

stop_bg backend
port="$(service_port backend)"
if port_up "$port"; then
  fail "backend still listening on $port"
fi
log "stopped"
