#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yaml"
ENV_FILE="$PROJECT_ROOT/.env"

cd "$PROJECT_ROOT"

if [ ! -x "$PYTHON_BIN" ]; then
    echo "Missing virtualenv python at $PYTHON_BIN"
    echo "Create it first, for example: python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt -r test_requirements.txt"
    exit 1
fi

if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

echo "Starting Postgres test dependency..."
docker compose -f "$COMPOSE_FILE" up -d database >/dev/null

echo "Waiting for Postgres on 127.0.0.1:5432..."
"$PYTHON_BIN" - <<'PY'
import socket
import time

deadline = time.time() + 30
last_error = None
while time.time() < deadline:
    try:
        with socket.create_connection(("127.0.0.1", 5432), timeout=1):
            raise SystemExit(0)
    except OSError as exc:
        last_error = exc
        time.sleep(1)

raise SystemExit(f"Postgres did not become reachable on 127.0.0.1:5432 within 30s: {last_error}")
PY

RUN_INTEGRATION_TESTS=1 exec "$PYTHON_BIN" -m pytest tests/integration -v -m "integration" "$@"
