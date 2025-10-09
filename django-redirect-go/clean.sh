#!/bin/bash
podman-compose down -v
podman-compose up --build -d
echo "Waiting for services to be ready..."
for i in {1..30}; do
  if curl -s http://localhost:8000/read > /dev/null 2>&1 && curl -s http://localhost:8001/read > /dev/null 2>&1; then
    echo "Services ready and database cleaned"
    exit 0
  fi
  sleep 1
done
echo "Services started"
