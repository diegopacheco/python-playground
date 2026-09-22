#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

log "tests started"
require uv
uv run ruff check . || fail "ruff check failed"
uv run ruff format --check . || fail "ruff format check failed"
uv run pytest -v || fail "pytest failed"
log "tests passed"
