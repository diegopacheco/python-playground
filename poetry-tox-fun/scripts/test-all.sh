#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

log "tests started"

require tox
tox || fail "tox failed"

log "tests passed"
