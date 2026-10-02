#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require_venv
MYPYPATH="$ROOT/src" "$ROOT/.venv/bin/mypy" --strict src tests scripts
"$PYTHON" -m unittest discover -s tests -t . -v
