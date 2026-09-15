#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

[ -x "$ROOT/.venv/bin/python" ] || fail "dependencies missing, run ./scripts/setup.sh first"
"$ROOT/.venv/bin/python" -m pytest -q || fail "backend tests failed"
log "tests passed"
