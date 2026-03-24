"""Reusable helpers for integration tests."""

import importlib
import os
import socket
import sys
import time
from contextlib import closing
from pathlib import Path

import psycopg2
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def reload_module(name: str):
    """Import or reload a project module after env var changes."""
    if name in sys.modules:
        return importlib.reload(sys.modules[name])
    return importlib.import_module(name)


def wait_for_http(url: str, timeout: float = 30.0):
    """Wait until an HTTP endpoint responds successfully."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=1)
            if response.ok:
                return response
        except requests.RequestException:
            pass
        time.sleep(0.5)
    raise TimeoutError(f"Timed out waiting for {url}")


def find_free_port() -> int:
    """Find a free localhost TCP port."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return sock.getsockname()[1]


def admin_db_config() -> dict[str, str]:
    """Build connection details for the Postgres admin database."""
    password = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError("Set DB_PASSWORD or POSTGRES_PASSWORD to run integration tests")

    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": os.getenv("DB_PORT", "5432"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": password,
        "dbname": os.getenv("DB_ADMIN_NAME", "postgres"),
    }


def connect(dbname: str | None = None, *, options: str = "-c timezone=Europe/Berlin"):
    """Open a psycopg2 connection with the integration test defaults."""
    config = admin_db_config()
    if dbname is not None:
        config["dbname"] = dbname
    return psycopg2.connect(**config, options=options)
