#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

log "setup started"

require uv
uv python install 3.15 || fail "uv could not install Python 3.15, run: uv self update"
uv sync || fail "uv sync failed"
"$PYTHON" -c 'import sys; raise SystemExit(sys.version_info < (3, 15, 0, "final"))' \
  || fail "$("$PYTHON" --version) is a pre-release, run: uv self update && uv python upgrade 3.15"

log "setup done: $("$PYTHON" --version), $("$VENV/bin/ruff" --version), $("$VENV/bin/ty" --version)"
