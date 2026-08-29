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

if ! podman exec bank_postgres psql -U bank_user -d bank_db -tAc \
    "select 1 from pg_database where datname = 'bank_test_db'" | grep -q 1; then
    podman exec bank_postgres createdb -U bank_user bank_test_db
fi

echo "postgres ready on localhost:5434, databases bank_db and bank_test_db"
