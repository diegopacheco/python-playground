#!/bin/bash

python3 src/main.py &
SERVER_PID=$!

until curl -s http://localhost:8000/ >/dev/null 2>&1; do
  sleep 1
done

echo "GET home"
curl -s http://localhost:8000/
echo ""
echo "GET tasks"
curl -s http://localhost:8000/tasks/
echo ""
echo "GET task detail"
curl -s http://localhost:8000/tasks/1/
echo ""

kill $SERVER_PID