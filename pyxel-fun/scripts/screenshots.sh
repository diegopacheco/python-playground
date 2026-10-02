#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require_venv
"$PYTHON" "$ROOT/scripts/screenshots.py"
echo "printscreens written to printscreens/"
