#!/bin/bash

python3 src/main.py &
SERVER_PID=$!

until curl -s http://localhost:5000/books >/dev/null 2>&1; do
  sleep 1
done

echo "GET all"
curl -s http://localhost:5000/books
echo ""
echo "POST create"
curl -s -X POST http://localhost:5000/books -H "Content-Type: application/json" -d '{"title":"The Pragmatic Programmer","author":"Hunt"}'
echo ""
echo "GET one"
curl -s http://localhost:5000/books/2
echo ""
echo "PUT replace"
curl -s -X PUT http://localhost:5000/books/2 -H "Content-Type: application/json" -d '{"title":"Refactoring","author":"Fowler"}'
echo ""
echo "PATCH update"
curl -s -X PATCH http://localhost:5000/books/2 -H "Content-Type: application/json" -d '{"author":"Martin Fowler"}'
echo ""
echo "DELETE"
curl -s -X DELETE http://localhost:5000/books/2
echo ""

kill $SERVER_PID