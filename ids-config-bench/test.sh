#!/bin/bash

VALID_ID="04317129-1eb7-4ed4-9cd0-86043412c45f"
INVALID_ID="99999999-9999-9999-9999-999999999999"

echo "Testing valid ID:"
curl -s "http://localhost:8000/check/$VALID_ID" | jq

echo -e "\nTesting invalid ID:"
curl -s "http://localhost:8000/check/$INVALID_ID" | jq