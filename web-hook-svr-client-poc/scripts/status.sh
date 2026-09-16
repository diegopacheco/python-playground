#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

down=0
printf "%-16s %-8s %-6s %s\n" SERVICE PORT STATE PID
for name in $(service_names); do
  port="$(service_port "$name")"
  pid="$(port_pid "$port")"
  if [ -n "$pid" ]; then
    printf "%-16s %-8s %-6s %s\n" "$name" "$port" UP "$pid"
  else
    printf "%-16s %-8s %-6s %s\n" "$name" "$port" DOWN "-"
    down=$((down + 1))
  fi
done

if port_up "$(service_port listener)"; then
  if listener_connected; then log "relay: connected"; else log "relay: not connected"; fi
fi

exit "$down"
