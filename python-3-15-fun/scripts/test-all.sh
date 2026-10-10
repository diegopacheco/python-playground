#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require_venv
log "tests started"

"$VENV/bin/ruff" check src tests || fail "lint failed"
"$VENV/bin/ty" check src tests || fail "type check failed"
PYTHONPATH="$ROOT/src" "$PYTHON" -m unittest discover -s tests -v || fail "unit tests failed"

log "tests passed"
