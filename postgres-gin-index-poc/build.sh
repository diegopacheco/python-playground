#!/bin/bash
set -e
cd "$(dirname "$0")"

PYTHON=${PYTHON:-python3.14}
command -v "$PYTHON" > /dev/null || PYTHON=python3
[ -x .venv/bin/python ] && PYTHON=.venv/bin/python

podman pull docker.io/library/postgres:18
podman pull docker.io/liquibase/liquibase:4.33
podman-compose build api
"$PYTHON" -m compileall -q src
echo "BUILD OK"
