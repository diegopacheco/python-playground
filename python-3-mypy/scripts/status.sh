#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

if [ -d "$ROOT/.venv" ]; then echo "venv: UP"; else echo "venv: DOWN"; fi
echo "mypyc compiled modules: $(compiled_count)"
if [ -f "$DB_FILE" ]; then
  echo "database: UP sqlite:///$DB_FILE"
  echo "migration: $(uv run alembic current 2>/dev/null | tail -1)"
else
  echo "database: DOWN"
fi
