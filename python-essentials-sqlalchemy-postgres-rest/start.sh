#!/bin/bash

podman-compose up -d

until podman exec python-essentials-sqlalchemy-postgres-rest_postgres_1 pg_isready -U postgres >/dev/null 2>&1; do
  sleep 1
done
echo "postgres ready"

python3 -m uvicorn src.main:app --host 127.0.0.1 --port 8000 >/tmp/sqlalchemy-rest.log 2>&1 &
echo $! > /tmp/sqlalchemy-rest.pid

until curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; do
  sleep 1
done
echo "api ready"
