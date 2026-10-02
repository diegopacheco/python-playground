#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

pid="$(game_pid)"
if [ -n "$pid" ]; then
  echo "game  window  UP    pid $pid"
else
  echo "game  window  DOWN  pid -"
fi
