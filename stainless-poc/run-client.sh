#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if ! .venv/bin/python -c "import taskly" >/dev/null 2>&1; then
  echo "the taskly sdk is not installed, run ./generate-sdk.sh first"
  exit 1
fi

exec .venv/bin/python client/main.py
