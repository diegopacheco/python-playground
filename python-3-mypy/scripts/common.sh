#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DB_FILE="$ROOT/library.db"
COMPILED_MODULES="library/service.py library/stats.py"

fail() {
  echo "error: $*" >&2
  exit 1
}

require() {
  command -v "$1" >/dev/null 2>&1 || fail "$1 is not installed"
}

compiled_count() {
  ls "$ROOT"/library/*.so 2>/dev/null | wc -l | tr -d ' '
}
