#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

[ -x "$ROOT/.venv/bin/python" ] || fail "missing venv, run scripts/setup.sh first"

exec "$ROOT/.venv/bin/python" "$SCRIPTS/posthog_dashboard.py" "$@"
