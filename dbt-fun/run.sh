#!/bin/bash

cd dbt_project
pip install dbt-postgres --quiet
export DBT_PROFILES_DIR=$(pwd)
python3 -m dbt.cli.main seed
python3 -m dbt.cli.main run
python3 -m dbt.cli.main docs generate

lsof -ti:8080 | xargs kill -9 2>/dev/null

echo "Starting dbt docs server on http://localhost:8080"
python3 -m dbt.cli.main docs serve --port 8080 &

sleep 1
open http://localhost:8080
