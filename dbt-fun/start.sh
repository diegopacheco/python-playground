#!/bin/bash

podman-compose down 2>/dev/null
podman-compose up -d

echo "Waiting for PostgreSQL to be ready..."
while ! podman exec dbt_postgres pg_isready -U dbt_user > /dev/null 2>&1; do
    sleep 1
done
echo "PostgreSQL is ready"
