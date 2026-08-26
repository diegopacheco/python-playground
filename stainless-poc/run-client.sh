#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if .venv/bin/python -c "import taskly" >/dev/null 2>&1; then
  echo "using the stainless sdk"
  exec .venv/bin/python client/main.py
fi

if .venv/bin/python -c "import taskly_offline" >/dev/null 2>&1; then
  echo "using the offline sdk"
  exec .venv/bin/python client/main_offline.py
fi

echo "no generated sdk installed, run ./generate-sdk.sh or ./generate-sdk-offline.sh first"
exit 1
