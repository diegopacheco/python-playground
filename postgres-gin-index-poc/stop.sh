#!/bin/bash
cd "$(dirname "$0")"

podman-compose down
echo "STOPPED"
