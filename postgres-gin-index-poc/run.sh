#!/bin/bash
set -e
cd "$(dirname "$0")"

PYTHON=.venv/bin/python
[ -x "$PYTHON" ] || { echo "run ./install-deps.sh first"; exit 1; }

export DB_HOST=${DB_HOST:-localhost}
export DB_PORT=${DB_PORT:-55432}
export API_PORT=${API_PORT:-8080}

"$PYTHON" src/main.py
