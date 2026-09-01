#!/bin/bash
set -e
cd "$(dirname "$0")"

podman-compose up -d postgres

echo "waiting for postgres"
for i in $(seq 1 60); do
  if podman exec gin-postgres pg_isready -U poc -d ginpoc > /dev/null 2>&1; then
    break
  fi
  sleep 1
done
podman exec gin-postgres pg_isready -U poc -d ginpoc

echo "running liquibase"
podman-compose run --rm liquibase

podman-compose up -d api

echo "waiting for api"
for i in $(seq 1 60); do
  if curl -s -f http://localhost:8080/health > /dev/null 2>&1; then
    break
  fi
  sleep 1
done
curl -s http://localhost:8080/health
echo
echo "STARTED"
