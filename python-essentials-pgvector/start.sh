#!/bin/bash

podman-compose up -d

until podman exec python-essentials-pgvector_postgres_1 pg_isready -U postgres >/dev/null 2>&1; do
  sleep 1
done
echo "postgres ready"
