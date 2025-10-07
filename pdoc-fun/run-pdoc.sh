#!/bin/bash

export PYTHONPATH="$(pwd):$(pwd)/src:${PYTHONPATH}"
pdoc --output-dir ./docs ./src