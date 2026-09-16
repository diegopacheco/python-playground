#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

HOUSES="${1:-5}"
MODELS="aspen birch cedar dune"
SERVER="http://localhost:$(service_port webhook_server)"

case "$HOUSES" in
  ''|*[!0-9]*) fail "usage: ./scripts/generate-synthetical-data.sh [number_of_houses]" ;;
esac

port_up "$(service_port webhook_server)" || fail "webhook_server is down, run ./scripts/start-all.sh first"
listener_connected || fail "listener is not connected to the relay, run ./scripts/start-all.sh first"

post() {
  curl -fsS -X POST -H 'Content-Type: application/json' -d "${2:-}" "$SERVER$1" || fail "POST $1 failed"
}

json_field() {
  python3 -c "import json, sys; print(json.load(sys.stdin)$1)"
}

i=1
while [ "$i" -le "$HOUSES" ]; do
  set -- $MODELS
  shift $((RANDOM % 4))
  model="$1"
  lot="$(printf 'Lot %s-%02d' "$(printf '%s' ABCDEF | cut -c $((RANDOM % 6 + 1)))" $((RANDOM % 40 + 1)))"
  alias="$(printf 'buyer-%04d' $((RANDOM % 10000)))"
  body="$(printf '{"model":"%s","lot":"%s","buyer_alias":"%s"}' "$model" "$lot" "$alias")"
  house_id="$(post /api/houses "$body" | json_field '["house"]["id"]')"
  log "house $i/$HOUSES $model $lot ordered"
  steps=$((RANDOM % 6 + 1))
  s=1
  while [ "$s" -le "$steps" ]; do
    event="$(post "/api/houses/$house_id/advance" | json_field '["event"]')"
    log "  house $i/$HOUSES $event"
    s=$((s + 1))
  done
  i=$((i + 1))
done

log "sent webhooks for $HOUSES synthetic houses, see $(service_url admin_ui)"
