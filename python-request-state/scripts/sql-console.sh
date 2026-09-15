#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require sqlite3
DB="${GAMES_DB_PATH:-$ROOT/games.db}"
[ -f "$DB" ] || fail "$DB does not exist, run ./scripts/start-all.sh first"
sqlite3 -header -column "$DB" "$@"
