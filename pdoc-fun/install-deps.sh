#!/bin/bash

export PYTHONPATH="${PYTHONPATH}:./src"
pdoc --output-dir ./docs ./src
