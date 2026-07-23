#!/bin/bash

./start.sh

echo "--- create ---"
curl -s -X POST http://127.0.0.1:8000/books -H 'Content-Type: application/json' -d '{"title":"Clean Code","author":"Robert Martin"}'
echo
curl -s -X POST http://127.0.0.1:8000/books -H 'Content-Type: application/json' -d '{"title":"Refactoring","author":"Martin Fowler"}'
echo
echo "--- list ---"
curl -s http://127.0.0.1:8000/books
echo
echo "--- get 1 ---"
curl -s http://127.0.0.1:8000/books/1
echo
echo "--- delete 1 ---"
curl -s -X DELETE http://127.0.0.1:8000/books/1
echo
echo "--- list after delete ---"
curl -s http://127.0.0.1:8000/books
echo
echo "--- swagger ui ---"
curl -s -o /dev/null -w "GET /docs -> %{http_code}\n" http://127.0.0.1:8000/docs

./stop.sh
