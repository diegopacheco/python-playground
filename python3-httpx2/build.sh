#!/bin/bash
set -e

python3.14 -m venv .venv
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt --quiet
.venv/bin/python --version
.venv/bin/python -c "import httpx2; print('httpx2', httpx2.__version__)"
.venv/bin/python -m compileall -q src tests
echo "build done"
