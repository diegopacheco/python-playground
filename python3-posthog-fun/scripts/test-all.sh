#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

[ -x "$ROOT/.venv/bin/python" ] || fail "missing venv, run scripts/setup.sh first"
[ -d "$ROOT/frontend/node_modules" ] || fail "missing frontend deps, run scripts/setup.sh first"

log "backend tests"
"$ROOT/.venv/bin/python" -m pytest "$ROOT/tests" -q || fail "backend tests failed"

log "frontend typecheck and build"
( cd "$ROOT/frontend" && bun run build ) || fail "frontend build failed"

log "all tests passed"
