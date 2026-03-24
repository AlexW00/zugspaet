#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"

cd "$PROJECT_ROOT"

if [ ! -x "$PYTHON_BIN" ]; then
    echo "Missing virtualenv python at $PYTHON_BIN"
    echo "Create it first, for example: python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt -r test_requirements.txt"
    exit 1
fi

exec "$PYTHON_BIN" -m pytest tests -v -m "not integration" "$@"
