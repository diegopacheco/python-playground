#!/bin/bash

curl -s -u guest:guest \
-H "content-type:application/json" \
http://127.0.0.1:15672/api/queues \
| jq '{ queues: map({name: .name, size: .messages_ready, consumers: .consumers})}'