#!/bin/bash
cd "$(dirname "$0")"

BASE=${BASE:-http://localhost:8080}
PASS=0
FAIL=0

jget() {
  python3 -c 'import json,sys
doc = json.loads(sys.argv[1])
for part in sys.argv[2].split("."):
    doc = doc[int(part)] if part.isdigit() else doc.get(part)
    if doc is None:
        break
print(doc)' "$1" "$2"
}

check_min() {
  if [ "$3" -ge "$2" ] 2>/dev/null; then
    echo "PASS $1"
    PASS=$((PASS + 1))
  else
    echo "FAIL $1 | expected at least [$2] got [$3]"
    FAIL=$((FAIL + 1))
  fi
}

check() {
  if [ "$2" = "$3" ]; then
    echo "PASS $1"
    PASS=$((PASS + 1))
  else
    echo "FAIL $1 | expected [$2] got [$3]"
    FAIL=$((FAIL + 1))
  fi
}

echo "the api is up and can reach postgres"
BODY=$(curl -s "$BASE/health")
check "health reports ok" "ok" "$(jget "$BODY" status)"
check_min "the liquibase seed rows are in the table" "50003" "$(jget "$BODY" documents)"

echo
echo "containment @> matches a nested jsonb subtree, not a string compare"
BODY=$(curl -s --get "$BASE/documents" \
  --data-urlencode 'contains={"category":"electronics","stock":{"warehouse":"wh-1"}}')
check "only the electronics item stored in wh-1 matches" "1" "$(jget "$BODY" count)"
check "the matched document is the laptop" "laptop-x1" "$(jget "$BODY" documents.0.name)"

echo
echo "key existence ? finds documents by the presence of a field alone"
BODY=$(curl -s --get "$BASE/documents" --data-urlencode 'key=discontinued')
check "only the discontinued desk has that key" "1" "$(jget "$BODY" count)"
check "the matched document is the desk" "desk-oak" "$(jget "$BODY" documents.0.name)"

echo
echo "any key ?| matches when at least one of the keys exists"
BODY=$(curl -s --get "$BASE/documents" --data-urlencode 'anyKey=discontinued,absent_field')
check "an absent key does not widen the result" "1" "$(jget "$BODY" count)"

echo
echo "the gin index is what answers a selective containment query on 50k rows"
BODY=$(curl -s --get "$BASE/explain" --data-urlencode 'contains={"sku":"SKU-4242"}')
check "planner chose a gin index" "True" "$(jget "$BODY" ginIndexUsed)"
echo "     indexes=$(jget "$BODY" indexes) time=$(jget "$BODY" executionTimeMs)ms"

echo
echo "a broad predicate is cheaper without the index, the planner is free to skip it"
BODY=$(curl -s --get "$BASE/explain" --data-urlencode 'contains={"brand":"brand-3"}')
echo "     INFO 2500 of 50000 rows match: indexes=$(jget "$BODY" indexes) time=$(jget "$BODY" executionTimeMs)ms"

echo
echo "the gin index also answers key existence queries"
BODY=$(curl -s --get "$BASE/explain" --data-urlencode 'key=discontinued')
check "planner chose a gin index" "True" "$(jget "$BODY" ginIndexUsed)"
echo "     indexes=$(jget "$BODY" indexes) time=$(jget "$BODY" executionTimeMs)ms"

echo
echo "a document written through the api is immediately searchable by the index"
SKU="SKU-RUN-$$"
BODY=$(curl -s -X POST "$BASE/documents" -H 'Content-Type: application/json' \
  -d "{\"name\":\"run-$$\",\"data\":{\"sku\":\"$SKU\",\"category\":\"test\",\"tags\":[\"fresh\"]}}")
NEW_ID=$(jget "$BODY" id)
check "post returns the stored id" "run-$$" "$(jget "$BODY" name)"
BODY=$(curl -s --get "$BASE/documents" --data-urlencode "contains={\"sku\":\"$SKU\"}")
check "the new document is found by containment" "1" "$(jget "$BODY" count)"
BODY=$(curl -s "$BASE/documents/$NEW_ID")
check "the new document is readable by id" "$SKU" "$(jget "$BODY" data.sku)"

echo
echo "bad input is rejected instead of reaching the database"
CODE=$(curl -s -o /dev/null -w "%{http_code}" --get "$BASE/documents" --data-urlencode 'contains=notjson')
check "malformed contains is a 400" "400" "$CODE"
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/documents/999999999")
check "missing document is a 404" "404" "$CODE"

echo
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
echo "TESTS OK"
