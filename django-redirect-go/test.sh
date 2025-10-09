#!/bin/bash
set -e
DJANGO_SAVE=$(curl -s -X POST http://localhost:8000/save -H "Content-Type: application/json" -d '{"number": 100, "date": "2025-10-09"}')
GO_SAVE=$(curl -s -X POST http://localhost:8001/save -H "Content-Type: application/json" -d '{"number": 200, "date": "2025-10-09"}')
echo "Django save: $DJANGO_SAVE"
echo "Go save: $GO_SAVE"
echo ""
DJANGO_READ=$(curl -s -X GET http://localhost:8000/read)
GO_READ=$(curl -s -X GET http://localhost:8001/read)
echo "Django read (django_schema): $DJANGO_READ"
echo "Go read (go_schema): $GO_READ"
echo ""
DJANGO_GETLAST=$(curl -s -L -X GET http://localhost:8000/getlast)
GO_GETLAST=$(curl -s -X GET http://localhost:8001/getlast)
echo "Django getlast (redirects to Go): $DJANGO_GETLAST"
echo "Go getlast (direct): $GO_GETLAST"
echo ""
if [ "$DJANGO_GETLAST" = "$GO_GETLAST" ]; then
    echo "SUCCESS: Django redirect to Go returns same result"
else
    echo "FAILED: Django redirect to Go returns different result"
    exit 1
fi
DJANGO_COUNT=$(echo $DJANGO_READ | grep -o '"id"' | wc -l | tr -d ' ')
GO_COUNT=$(echo $GO_READ | grep -o '"id"' | wc -l | tr -d ' ')
echo "Django schema record count: $DJANGO_COUNT"
echo "Go schema record count: $GO_COUNT"
if [ "$DJANGO_COUNT" -gt "0" ] && [ "$GO_COUNT" -gt "0" ]; then
    echo "SUCCESS: Both apps writing and reading from separate schemas"
else
    echo "FAILED: One or both apps not working"
    exit 1
fi
