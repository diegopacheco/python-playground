#!/bin/bash
set -e
cd "$(dirname "$0")"

./db-start.sh
.venv/bin/python -m pytest tests -v
