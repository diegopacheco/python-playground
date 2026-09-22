#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require uv
uv run alembic upgrade head || fail "alembic migration failed"
uv run library || fail "library app failed"
log "database: sqlite:///library.db"
