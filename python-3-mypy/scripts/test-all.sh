#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

[ -d "$ROOT/.venv" ] || fail "run scripts/setup.sh first"
uv run ruff check . || fail "ruff lint failed"
uv run ruff format --check . || fail "ruff format failed"
uv run mypy library tests migrations || fail "mypy failed"
uv run pytest -v || fail "pytest failed"
