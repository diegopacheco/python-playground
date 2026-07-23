#!/bin/bash
set -e

podman-compose up -d

until podman run --rm --network host temporalio/temporal:latest workflow list --address localhost:7233 >/dev/null 2>&1; do
  echo "waiting for temporal..."
  sleep 1
done

echo "temporal is up on localhost:7233 (UI: http://localhost:8233)"
