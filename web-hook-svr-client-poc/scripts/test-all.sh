#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require python3
log "running unit and integration tests"
python3 -m unittest discover -s tests -t . -v || fail "tests failed"
