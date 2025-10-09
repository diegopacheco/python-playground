#!/bin/bash
echo "Testing Django app (port 8000)..."
curl -X POST http://localhost:8000/save -H "Content-Type: application/json" -d '{"number": 42, "date": "2025-10-08"}'
echo ""
curl -X GET http://localhost:8000/read
echo ""
echo ""
echo "Testing Go app (port 8001)..."
curl -X POST http://localhost:8001/save -H "Content-Type: application/json" -d '{"number": 42, "date": "2025-10-08"}'
echo ""
curl -X GET http://localhost:8001/read
echo ""
echo ""
echo "Testing /getlast endpoint..."
echo "Django (redirects to Go):"
curl -L -X GET http://localhost:8000/getlast
echo ""
echo "Go (direct):"
curl -X GET http://localhost:8001/getlast
echo ""
