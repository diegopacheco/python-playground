#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

log "type check started"

require tox
tox -e types || fail "ty type check failed"

log "type check passed"
