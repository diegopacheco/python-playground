#!/bin/bash
pip install dagster dagster-webserver
cd src/
open http://127.0.0.1:3000
dagster dev -f main.py
