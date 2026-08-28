#!/bin/bash
set -e

PORT=${PORT:-8080}
BASE_URL="http://127.0.0.1:$PORT"
STARTED=""

if ! .venv/bin/python -c "import socket,sys; sys.exit(0 if socket.socket().connect_ex(('127.0.0.1', $PORT)) == 0 else 1)"; then
    .venv/bin/python src/server.py "$PORT" &
    STARTED=$!
    for _ in $(seq 1 30); do
        if .venv/bin/python -c "import socket,sys; sys.exit(0 if socket.socket().connect_ex(('127.0.0.1', $PORT)) == 0 else 1)"; then
            break
        fi
        sleep 1
    done
fi

.venv/bin/python src/main.py "$BASE_URL"

if [ -n "$STARTED" ]; then
    kill "$STARTED"
    wait "$STARTED" 2>/dev/null || true
fi

echo "client run done"
