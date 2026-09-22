#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

port="$(service_port router)"
[ -n "$port" ] || fail "router is not declared in scripts/ports.env"

url="$(service_url router)"
port_up "$port" || fail "router is not running on $port, run ./scripts/start-all.sh first"

log "opening $url"
open_url "$url"
