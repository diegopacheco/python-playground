#!/bin/bash
set -e

cd "$(dirname "$0")"
.venv/bin/python src/main.py
