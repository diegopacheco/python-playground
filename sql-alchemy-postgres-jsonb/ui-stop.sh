#!/bin/bash
cd "$(dirname "$0")"

if [ ! -f .ui.pid ]; then
    echo "ui not running"
    exit 0
fi

kill "$(cat .ui.pid)" 2>/dev/null
rm -f .ui.pid
echo "ui stopped"
