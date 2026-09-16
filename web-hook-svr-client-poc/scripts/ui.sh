#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

port="$(service_port admin_ui)"
port_up "$port" || fail "admin_ui is not running on $port, run ./scripts/start-all.sh first"

url="$(service_url admin_ui)"
log "opening $url"
open_url "$url"
