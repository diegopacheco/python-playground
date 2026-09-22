#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

[ -d "$ROOT/.venv" ] || fail "run scripts/setup.sh first"
uv run alembic upgrade head || fail "alembic upgrade failed"
uv run python -m library.main || fail "library app failed"
echo "database: sqlite:///$DB_FILE"
