#!/bin/bash
set -e
cd "$(dirname "$0")"

./db-start.sh
./ui-start.sh
