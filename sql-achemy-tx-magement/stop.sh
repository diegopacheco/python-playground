#!/bin/bash
cd "$(dirname "$0")"

if [ -f .api.pid ]; then
    kill "$(cat .api.pid)" 2>/dev/null
    rm -f .api.pid
    echo "api stopped"
fi

podman-compose down
echo "postgres stopped"
