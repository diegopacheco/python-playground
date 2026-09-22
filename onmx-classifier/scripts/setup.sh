#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

log "setup started"
require uv
uv sync || fail "uv sync failed"
uv run onnx-router-train || fail "model training failed"
log "setup done"
