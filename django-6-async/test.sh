#!/bin/bash
set -e

.venv/bin/python manage.py test tests -v 2
