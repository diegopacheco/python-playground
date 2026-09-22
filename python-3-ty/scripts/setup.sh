#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require uv
uv python find 3.14.7 >/dev/null || uv python install 3.14.7 || fail "python 3.14.7 is required"
uv sync || fail "uv sync failed"
uv run alembic upgrade head || fail "alembic migration failed"
log "setup done, database at sqlite:///library.db"
