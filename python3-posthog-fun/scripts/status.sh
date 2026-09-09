#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

for name in $(service_names); do
  port="$(service_port "$name")"
  pid="$(port_pid "$port")"
  if [ -n "$pid" ]; then
    printf "%-10s port %-6s UP    pid %s\n" "$name" "$port" "$pid"
  else
    printf "%-10s port %-6s DOWN\n" "$name" "$port"
  fi
done
