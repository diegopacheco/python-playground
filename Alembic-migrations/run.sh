#!/bin/bash
set -e

podman-compose up -d

echo "Waiting for PostgreSQL to be ready..."
while ! podman exec alembic_postgres pg_isready -U alembic_user > /dev/null 2>&1; do
    sleep 1
done
echo "PostgreSQL is ready"

.venv/bin/alembic upgrade head
.venv/bin/alembic current
