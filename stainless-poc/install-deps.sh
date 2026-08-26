#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python3.14}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "$PYTHON_BIN not found, install Python $(cat .python-version)"
  exit 1
fi

VERSION="$("$PYTHON_BIN" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
if [ "$VERSION" != "3.14" ]; then
  echo "$PYTHON_BIN is $VERSION, this project needs 3.14"
  exit 1
fi

"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
echo "venv ready with $(.venv/bin/python --version)"
