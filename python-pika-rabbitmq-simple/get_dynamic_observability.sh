#!/bin/bash

curl -s -u guest:guest \
-H "content-type:application/json" \
http://127.0.0.1:15672/api/queues \
| jq '{ messages: map(.name, .messages_ready), consumers: map(.name, .consumers) }'