#!/bin/bash

OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2}"
EMBED_MODEL="${OLLAMA_EMBED_MODEL:-nomic-embed-text}"

if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  ollama serve >/tmp/ollama-serve.log 2>&1 &
  echo $! > /tmp/ollama-serve.pid
  until curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; do
    sleep 1
  done
fi
echo "ollama ready"

ollama pull "$OLLAMA_MODEL"
ollama pull "$EMBED_MODEL"
