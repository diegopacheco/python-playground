#!/bin/bash

app=$(pwd)
export PYTHONPATH="${PYTHONPATH}:$app/src/"
uvicorn main:app --reload
