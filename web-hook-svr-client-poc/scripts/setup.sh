#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

require python3
require curl
require lsof
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || fail "python 3.10 or newer is required"

if [ -f "$RELAY_ENV" ]; then
  log "relay already configured"
else
  channel="$(curl -fsS -o /dev/null -w '%{redirect_url}' https://smee.io/new)" || fail "could not reach smee.io"
  [ -n "$channel" ] || fail "smee.io did not return a channel"
  secret="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
  umask 077
  printf "RELAY_URL=%s\nWEBHOOK_SECRET=%s\n" "$channel" "$secret" >"$RELAY_ENV"
  log "relay channel and webhook secret created"
fi

log "setup done, no third party python packages needed"
