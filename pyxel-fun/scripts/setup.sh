#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

if ! command -v python3.14 >/dev/null 2>&1; then
  echo "python3.14 not found on PATH" >&2
  exit 1
fi
if [ ! -x "$PYTHON" ]; then
  python3.14 -m venv "$ROOT/.venv"
fi
"$PYTHON" -m pip install -q -r "$ROOT/requirements.txt"
echo "setup done: $("$PYTHON" --version), pyxel $("$PYTHON" -c 'import pyxel; print(pyxel.VERSION)')"
