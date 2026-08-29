#!/bin/bash
set -e
cd "$(dirname "$0")"

./db-start.sh

if [ -f .api.pid ] && kill -0 "$(cat .api.pid)" 2>/dev/null; then
    echo "api already running on http://localhost:8000 (pid $(cat .api.pid))"
    exit 0
fi

.venv/bin/uvicorn controller:app --app-dir src --host 127.0.0.1 --port 8000 > .api.log 2>&1 &
echo $! > .api.pid

attempts=0
until curl -sf http://localhost:8000/ > /dev/null 2>&1; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge 30 ]; then
        echo "api did not start in 30s"
        cat .api.log
        rm -f .api.pid
        exit 1
    fi
    sleep 1
done

echo "api ready on http://localhost:8000"
