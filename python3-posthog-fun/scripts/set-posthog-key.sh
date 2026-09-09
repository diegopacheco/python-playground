#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

VARIABLE="POSTHOG_PERSONAL_API_KEY"
TARGET="$ROOT/.env"

printf "Paste your PostHog Personal API key (input hidden), then press enter:\n> "
read -rs KEY
printf "\n"

[ -n "$KEY" ] || fail "nothing entered"

case "$KEY" in
  *your_key_here*) fail "that is the placeholder text, paste the real key from PostHog" ;;
  phx_*) ;;
  *) fail "a PostHog personal API key starts with phx_, got something else" ;;
esac

[ "${#KEY}" -ge 30 ] || fail "key looks too short at ${#KEY} chars, expected 40 or more"

touch "$TARGET"
if [ -s "$TARGET" ] && [ "$(tail -c 1 "$TARGET" | wc -l | tr -d ' ')" -eq 0 ]; then
  printf "\n" >>"$TARGET"
fi

TEMP="$(mktemp)"
grep -v "^${VARIABLE}=" "$TARGET" >"$TEMP" || true
printf "%s=%s\n" "$VARIABLE" "$KEY" >>"$TEMP"
mv "$TEMP" "$TARGET"
chmod 600 "$TARGET"

log "stored $VARIABLE (${#KEY} chars, starts ${KEY:0:4}) in the local env file"
log "the key was never printed and the file stays git-ignored"
log "next: .venv/bin/python scripts/posthog_dashboard.py"
