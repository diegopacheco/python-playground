#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  ./install-deps.sh
fi

if [ -z "${STAINLESS_API_KEY:-}" ]; then
  echo "STAINLESS_API_KEY is not set, create one at https://app.stainless.com"
  exit 1
fi

if [ -z "${STAINLESS_ORG:-}" ]; then
  echo "STAINLESS_ORG is not set, use your Stainless organization name"
  exit 1
fi

.venv/bin/python tools/stainless_build.py
.venv/bin/pip install ./sdk
echo "generated sdk installed as $(.venv/bin/python -c 'import taskly; print(taskly.__name__)')"
