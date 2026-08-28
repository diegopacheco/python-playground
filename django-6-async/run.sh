#!/bin/bash
set -e

.venv/bin/python manage.py migrate --noinput
echo "Async Bank on http://127.0.0.1:8000"
exec .venv/bin/uvicorn config.asgi:application --host 127.0.0.1 --port 8000
