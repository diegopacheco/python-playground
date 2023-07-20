#!/bin/bash

#| jq '.[] |[.consumers, .name, .messages_ready]'

curl -s -u guest:guest \
-H "content-type:application/json" \
http://127.0.0.1:15672/api/queues \
| jq '{ queues: map(.name), messages: map(.messages_ready), consumers: map(.consumers) }'