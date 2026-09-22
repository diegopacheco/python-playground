#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require uv
log "ruff format"
uv run ruff format --check . || fail "ruff format check failed"
log "ruff lint"
uv run ruff check . || fail "ruff lint failed"
log "ty check"
uv run ty check || fail "ty type check failed"
log "ty must reject broken/"
if uv run ty check --config 'src.include=["broken"]' >/dev/null 2>&1; then
  fail "ty did not report errors in broken/"
fi
log "ty rejected broken/ as expected"
log "pytest"
uv run pytest -q || fail "pytest failed"
