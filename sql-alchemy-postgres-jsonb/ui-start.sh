#!/bin/bash
set -e
cd "$(dirname "$0")"

if [ -f .ui.pid ] && kill -0 "$(cat .ui.pid)" 2>/dev/null; then
    echo "ui already running on http://localhost:8000 (pid $(cat .ui.pid))"
    exit 0
fi

.venv/bin/uvicorn app:app --app-dir src --host 127.0.0.1 --port 8000 > .ui.log 2>&1 &
echo $! > .ui.pid

attempts=0
until curl -sf http://localhost:8000/ > /dev/null 2>&1; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge 30 ]; then
        echo "ui did not start in 30s"
        cat .ui.log
        rm -f .ui.pid
        exit 1
    fi
    sleep 1
done

echo "ui ready on http://localhost:8000"
