#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_IMAGE="${PYTHON_IMAGE:-python:3.11-slim}"

docker run --rm \
  -v "${SCRIPT_DIR}:/work" \
  -w /work \
  "${PYTHON_IMAGE}" \
  sh -lc '
    pip install --no-cache-dir pip-tools >/dev/null &&
    pip-compile \
      --strip-extras \
      --resolver=backtracking \
      --output-file requirements.lock \
      requirements.txt
  '
