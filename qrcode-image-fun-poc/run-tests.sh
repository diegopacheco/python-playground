#!/bin/bash
set -e

cd "$(dirname "$0")"
.venv/bin/python -m unittest discover -s tests -v
