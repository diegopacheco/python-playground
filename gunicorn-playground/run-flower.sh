#!/bin/bash

# Start Celery worker
celery -A src.main.celery_app worker --loglevel=info &

# Start Flower to monitor Celery tasks
celery -A src.main.celery_app flower