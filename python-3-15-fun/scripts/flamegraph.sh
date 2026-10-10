#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require_venv
mkdir -p "$ROOT/.run"

if [ "$(uname)" = "Darwin" ]; then
  log "Tachyon reads another process memory, macOS asks for sudo"
  sudo PYTHONDONTWRITEBYTECODE=1 "$PYTHON" src/profiling_sampling.py || fail "sampling profiler failed"
  sudo chown "$(id -u)" "$ROOT/.run/flamegraph.html"
else
  "$PYTHON" src/profiling_sampling.py || fail "sampling profiler failed"
fi
