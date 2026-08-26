#!/bin/bash
cd "$(dirname "$0")"

./ui-stop.sh
podman-compose down -v
echo "ui stopped, postgres stopped, volume removed"
