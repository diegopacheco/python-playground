#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

mkdir -p target
uv run pytest workload -n 2 --dist worksteal -p worksteal.plugin --steal-report=target/steal.json -v
uv run python -c '
import json, sys
ledger = json.load(open("target/steal.json"))
stolen = [(s["victim"], t) for s in ledger["steals"] for t in s["tests"]]
moved = [t for v, t in stolen if ledger["runs"][t] != v]
print(f"stolen tests: {len(stolen)}  ran on another worker: {len(moved)}")
sys.exit(0 if moved else 1)
'
