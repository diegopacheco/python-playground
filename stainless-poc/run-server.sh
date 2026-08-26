#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  ./install-deps.sh
fi

exec .venv/bin/python server/main.py
