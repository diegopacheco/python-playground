#!/bin/bash
set -e
cd "$(dirname "$0")"

PYTHON=${PYTHON:-python3.14}
command -v "$PYTHON" > /dev/null || PYTHON=python3

"$PYTHON" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python --version
