#!/bin/bash

main() {
  podman pull nikolaik/python-nodejs:python3.13-nodejs24 &&
    podman run --rm -it \
      -v $(pwd):/workspace \
      -e UV_CACHE_DIR=/workspace/.uv-cache \
      -e UV_TOOL_DIR=/workspace/.uv-tools \
      -e UV_DATA_DIR=/workspace/.uv-data \
      --user $(id -u):$(id -g) \
      nikolaik/python-nodejs:python3.13-nodejs24 \
      bash -c "cd /workspace && uv tool run cruft create https://github.com/hyperflask/hyperflask-start" \
      </dev/tty
}

main
