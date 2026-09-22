#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require uv
uv sync || fail "uv sync failed"
uv run mypy library tests migrations || fail "mypy failed"
uv run mypyc $COMPILED_MODULES || fail "mypyc build failed"
uv run alembic upgrade head || fail "alembic upgrade failed"
echo "setup done: $(compiled_count) compiled modules, database at sqlite:///library.db"
