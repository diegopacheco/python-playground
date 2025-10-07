#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Usage: $0 <repository_path> [--dry-run]"
    exit 1
fi

PYTHON=/usr/bin/python3
SCRIPT_DIR=/Users/diegopacheco/Documents/git/diegopacheco/python-playground/auto-commit
SCRIPT=$SCRIPT_DIR/auto-commit.py

$PYTHON $SCRIPT "$@"