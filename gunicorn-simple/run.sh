#!/bin/bash

gunicorn -w 2 main:app --chdir src/