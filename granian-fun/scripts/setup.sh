#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

log "setup started"

require python3.14
if [ ! -x "$PYTHON" ]; then
  python3.14 -m venv "$VENV"
fi
"$PYTHON" -m pip install -q -r "$ROOT/requirements.txt"

log "setup done: $("$PYTHON" --version), $("$VENV/bin/granian" --version)"
