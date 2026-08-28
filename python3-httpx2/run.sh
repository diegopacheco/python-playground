#!/bin/bash
set -e

PORT=${PORT:-8080}
.venv/bin/python src/server.py "$PORT"
