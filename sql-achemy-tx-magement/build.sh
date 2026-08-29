#!/bin/bash
set -e
cd "$(dirname "$0")"

python3.14 -m venv .venv
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt --quiet
.venv/bin/python --version
.venv/bin/python -m compileall -q src tests
echo "build done"
