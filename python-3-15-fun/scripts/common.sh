#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
PYTHON="$VENV/bin/python"
cd "$ROOT"

require() {
  command -v "$1" >/dev/null 2>&1 || fail "$1 is required but not installed"
}

require_venv() {
  [ -x "$PYTHON" ] || fail "virtualenv is missing, run ./scripts/setup.sh first"
}

log() {
  printf "%s\n" "$*"
}

fail() {
  printf "ERROR: %s\n" "$*" >&2
  exit 1
}
