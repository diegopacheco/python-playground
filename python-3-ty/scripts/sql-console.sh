#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require sqlite3
[ -f "$DB_FILE" ] || fail "no database file, run scripts/setup.sh"
exec sqlite3 -header -column "$DB_FILE" "$@"
