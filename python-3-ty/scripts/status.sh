#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require uv
if [ ! -f "$DB_FILE" ]; then
  log "sqlite   sqlite:///library.db   DOWN   no database file, run scripts/setup.sh"
  exit 0
fi
revision="$(uv run alembic current 2>/dev/null | tail -1)"
books="$(sqlite3 "$DB_FILE" "select count(*) from books;" 2>/dev/null || echo 0)"
log "sqlite   sqlite:///library.db   UP   revision ${revision:-none}   books $books"
