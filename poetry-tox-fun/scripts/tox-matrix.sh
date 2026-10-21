#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

VERSIONS="3.13 3.14 3.15"

log "matrix started: Python $VERSIONS"

require uv
require tox
for version in $VERSIONS; do
  uv python install "$version" || fail "uv could not install Python $version"
done

tox run-parallel -m matrix --parallel-live || fail "tox matrix failed"

log "matrix passed on Python $VERSIONS"
