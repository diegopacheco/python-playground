#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -d .venv ]; then
  uv venv .venv --python 3.13
fi
uv pip install --python .venv/bin/python -r requirements.txt

cd web
bun install
bun run build

echo "build done: $ROOT/web/dist"
