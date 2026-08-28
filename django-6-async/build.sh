#!/bin/bash
set -e

python3.14 -m venv .venv
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt --quiet
.venv/bin/python manage.py migrate --noinput
echo "build done"
