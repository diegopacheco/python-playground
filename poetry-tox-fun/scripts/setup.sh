#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

log "setup started"

require uv
uv python install 3.15 || fail "uv could not install Python 3.15"
command -v poetry >/dev/null 2>&1 || uv tool install poetry --python 3.15 || fail "uv could not install poetry"
command -v tox >/dev/null 2>&1 || uv tool install tox --with tox-uv --python 3.15 || fail "uv could not install tox"

poetry env use "$(uv python find 3.15)" >/dev/null || fail "poetry could not use Python 3.15"
poetry install || fail "poetry install failed"

log "setup done: $("$VENV/bin/python" --version), $(poetry --version), tox $(tox --version | head -1 | cut -d' ' -f1)"
