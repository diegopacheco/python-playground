#!/bin/bash
set -e

podman-compose up -d

attempts=0
until podman exec jsonb_postgres pg_isready -U jsonb_user -d jsonb_db > /dev/null 2>&1; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge 60 ]; then
        echo "postgres did not become ready in 60s"
        exit 1
    fi
    sleep 1
done

echo "postgres ready on localhost:5433"
