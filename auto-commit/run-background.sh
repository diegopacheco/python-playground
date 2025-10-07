#!/bin/bash
if [ $# -eq 0 ]; then
    echo "Usage: $0 <repository_path>"
    exit 1
fi
/usr/bin/python3 /Users/diegopacheco/Documents/git/diegopacheco/python-playground/auto-commit/auto-commit.py "$1"
