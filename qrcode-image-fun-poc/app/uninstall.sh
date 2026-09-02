#!/bin/bash
set -e

cd "$(dirname "$0")"

APP_NAME="QR Page Capture"
INSTALLED="/Applications/${APP_NAME}.app"

osascript -e "tell application \"${APP_NAME}\" to quit" 2>/dev/null || true
for _ in 1 2 3 4 5 6 7 8 9 10; do
  pgrep -f "${INSTALLED}" >/dev/null || break
  sleep 0.5
done
pkill -9 -f "${INSTALLED}" 2>/dev/null || true

if [ -d "${INSTALLED}" ]; then
  rm -rf "${INSTALLED}"
  echo "removed ${INSTALLED}"
else
  echo "nothing installed at ${INSTALLED}"
fi

rm -rf dist

if [ "$1" != "--keep-state" ]; then
  rm -rf "${HOME}/Library/Application Support/${APP_NAME}"
fi

echo "uninstall done"
