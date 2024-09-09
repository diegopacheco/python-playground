#!/bin/bash

gunicorn -w 4 src.main:app