#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require python3.14
require bun

if [ ! -x "$ROOT/.venv/bin/python" ]; then
  log "creating venv with python3.14"
  python3.14 -m venv "$ROOT/.venv"
fi

log "installing backend dependencies"
"$ROOT/.venv/bin/pip" install --quiet --upgrade pip
"$ROOT/.venv/bin/pip" install --quiet -r "$ROOT/requirements.txt" -r "$ROOT/requirements-dev.txt"

log "installing frontend dependencies"
( cd "$ROOT/frontend" && bun install )

log "setup done"
