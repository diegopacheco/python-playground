#!/bin/bash

lsof -nP -tiTCP:8000 -sTCP:LISTEN | xargs -r kill 2>/dev/null

python3 -m uvicorn src.main:app --host 127.0.0.1 --port 8000
