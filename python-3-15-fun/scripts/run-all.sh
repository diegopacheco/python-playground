#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require_venv
"$PYTHON" src/main.py || fail "a feature failed"
