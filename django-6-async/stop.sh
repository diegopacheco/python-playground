#!/bin/bash
pkill -f "uvicorn config.asgi:application" && echo "stopped" || echo "not running"
