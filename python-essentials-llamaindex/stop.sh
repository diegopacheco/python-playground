#!/bin/bash

if [ -f /tmp/ollama-serve.pid ]; then
  kill "$(cat /tmp/ollama-serve.pid)" 2>/dev/null
  rm -f /tmp/ollama-serve.pid
fi
