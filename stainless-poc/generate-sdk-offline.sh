#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  ./install-deps.sh
fi

.venv/bin/pip install --quiet openapi-python-client
PATH="$PWD/.venv/bin:$PATH" .venv/bin/openapi-python-client generate \
  --path api/openapi.yml \
  --config api/openapi-python-client.yml \
  --output-path sdk-offline \
  --overwrite
.venv/bin/pip install --quiet ./sdk-offline
echo "generated sdk installed as $(.venv/bin/python -c 'import taskly_offline; print(taskly_offline.__name__)')"
