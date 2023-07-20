#!/bin/bash

cat metrics.json|  jq '.[] |[.consumers, .name, .messages_ready]'
