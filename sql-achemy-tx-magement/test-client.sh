#!/bin/bash
set -e
cd "$(dirname "$0")"

BASE_URL="http://localhost:8000"

./start.sh

SOURCE=$(curl -sf -X POST "$BASE_URL/api/accounts" -H 'Content-Type: application/json' \
    -d '{"owner":"alice-'"$RANDOM"'","initial_balance":"100.00"}' | .venv/bin/python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
TARGET=$(curl -sf -X POST "$BASE_URL/api/accounts" -H 'Content-Type: application/json' \
    -d '{"owner":"bob-'"$RANDOM"'","initial_balance":"0.00"}' | .venv/bin/python -c 'import json,sys; print(json.load(sys.stdin)["id"])')

echo "accounts: source=$SOURCE target=$TARGET"

echo "--- transfer 30.00 (commits) ---"
curl -sf -X POST "$BASE_URL/api/transfers" -H 'Content-Type: application/json' \
    -d '{"source_id":'"$SOURCE"',"target_id":'"$TARGET"',"amount":"30.00"}'
echo
curl -sf "$BASE_URL/api/accounts/$SOURCE"; echo
curl -sf "$BASE_URL/api/accounts/$TARGET"; echo

echo "--- transfer 500.00 (rolls back, insufficient funds) ---"
curl -s -o /dev/stderr -w 'http %{http_code}\n' -X POST "$BASE_URL/api/transfers" \
    -H 'Content-Type: application/json' \
    -d '{"source_id":'"$SOURCE"',"target_id":'"$TARGET"',"amount":"500.00"}'
echo
curl -sf "$BASE_URL/api/accounts/$SOURCE"; echo
curl -sf "$BASE_URL/api/accounts/$TARGET"; echo

echo "--- transfer to a missing account (rolls back the debit) ---"
curl -s -o /dev/stderr -w 'http %{http_code}\n' -X POST "$BASE_URL/api/transfers" \
    -H 'Content-Type: application/json' \
    -d '{"source_id":'"$SOURCE"',"target_id":999999,"amount":"10.00"}'
echo
curl -sf "$BASE_URL/api/accounts/$SOURCE"; echo

echo "--- ledger ---"
curl -sf "$BASE_URL/api/ledger"; echo

echo "client run done"
