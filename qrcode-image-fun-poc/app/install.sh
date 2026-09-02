#!/bin/bash
set -e

cd "$(dirname "$0")"

APP_NAME="QR Page Capture"
INSTALLED="/Applications/${APP_NAME}.app"

./uninstall.sh --keep-state

[ -d node_modules ] || npm install
[ -f resources/icon.icns ] || ../.venv/bin/python resources/make-icon.py

npm run package

cp -R "dist/${APP_NAME}-darwin-arm64/${APP_NAME}.app" "${INSTALLED}"
rm -rf dist

xattr -dr com.apple.quarantine "${INSTALLED}" 2>/dev/null || true

echo "installed ${INSTALLED}"
