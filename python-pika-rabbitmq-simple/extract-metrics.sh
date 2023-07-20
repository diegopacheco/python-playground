#!/bin/bash

cat metrics.json \
| jq '{ queues: map({name: .name, size: .messages_ready, consumers: .consumers})}'