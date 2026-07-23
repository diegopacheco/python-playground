#!/bin/bash

if [ -f /tmp/sqlalchemy-rest.pid ]; then
  kill "$(cat /tmp/sqlalchemy-rest.pid)" 2>/dev/null
  rm -f /tmp/sqlalchemy-rest.pid
fi
podman-compose down
