#!/bin/bash
set -e
cd "$(dirname "$0")"

podman-compose up -d

attempts=0
until podman exec bank_postgres pg_isready -U bank_user -d bank_db > /dev/null 2>&1; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge 60 ]; then
        echo "postgres did not become ready in 60s"
        exit 1
    fi
    sleep 1
done

echo "postgres ready on localhost:5434"
