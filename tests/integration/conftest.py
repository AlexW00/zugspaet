"""Shared fixtures for integration tests."""

import csv
import os
import subprocess
import sys
import uuid

import pytest

from tests.integration.helpers import PROJECT_ROOT, connect, find_free_port, reload_module, wait_for_http


@pytest.fixture(scope="session", autouse=True)
def require_integration_opt_in():
    """Integration tests are opt-in so unit test runs stay fast and isolated."""
    if os.getenv("RUN_INTEGRATION_TESTS") != "1":
        pytest.skip("Set RUN_INTEGRATION_TESTS=1 to run integration tests", allow_module_level=True)


@pytest.fixture
def isolated_database():
    """Create a dedicated temporary database for one integration test."""
    db_name = f"zugspaet_it_{uuid.uuid4().hex[:8]}"

    admin_conn = connect()
    admin_conn.autocommit = True
    try:
        with admin_conn.cursor() as cur:
            cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
            cur.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        admin_conn.close()

    try:
        yield db_name
    finally:
        admin_conn = connect()
        admin_conn.autocommit = True
        try:
            with admin_conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = %s AND pid <> pg_backend_pid()
                    """,
                    (db_name,),
                )
                cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
        finally:
            admin_conn.close()


@pytest.fixture
def integration_environment(monkeypatch, isolated_database, tmp_path):
    """Prepare isolated env vars and folders for a full pipeline integration test."""
    xml_dir = tmp_path / "xml"
    eva_dir = tmp_path / "eva"
    xml_dir.mkdir()
    eva_dir.mkdir()

    env = {
        "DB_HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "DB_PORT": os.getenv("DB_PORT", "5432"),
        "DB_NAME": isolated_database,
        "DB_USER": os.getenv("DB_USER", "postgres"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", ""),
        "DB_OPTIONS": "-c timezone=Europe/Berlin",
        "XML_DIR": str(xml_dir),
        "EVA_DIR": str(eva_dir),
        "PRIVATE_API_KEY": os.getenv("PRIVATE_API_KEY", "integration-private-key"),
        "BASE_URL": "http://127.0.0.1",
        "PRODUCTION": "true",
    }

    for key, value in env.items():
        monkeypatch.setenv(key, value)

    reload_module("config")
    db_utils = reload_module("db_utils")
    db_utils.init_database()

    return {
        "db_name": isolated_database,
        "xml_dir": xml_dir,
        "eva_dir": eva_dir,
        "env": env,
    }


@pytest.fixture
def live_api_credentials():
    """Load Deutsche Bahn API credentials or skip the live API test."""
    api_key = os.getenv("API_KEY")
    client_id = os.getenv("CLIENT_ID")
    if not api_key or not client_id:
        pytest.skip("Live API integration test requires API_KEY and CLIENT_ID")
    return {"api_key": api_key, "client_id": client_id}


@pytest.fixture
def boeblingen_eva_file(integration_environment):
    """Create a one-station EVA file for Böblingen to keep the live import fast."""
    source_path = PROJECT_ROOT / "current_eva_list.csv"
    target_path = integration_environment["eva_dir"] / "current_eva_list.csv"

    with source_path.open(newline="") as source_handle:
        reader = csv.DictReader(source_handle)
        rows = [row for row in reader if row["name"] == "Böblingen"]

    if not rows:
        raise RuntimeError("Could not find Böblingen in current_eva_list.csv")

    with target_path.open("w", newline="") as target_handle:
        writer = csv.DictWriter(target_handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    return target_path


@pytest.fixture
def started_server(integration_environment):
    """Run the Flask app in a subprocess against the isolated integration database."""
    port = find_free_port()
    server_env = os.environ.copy()
    server_env.update(integration_environment["env"])
    server_env["BASE_URL"] = f"http://127.0.0.1:{port}"
    server_env["PYTHONUNBUFFERED"] = "1"

    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            f"import server; server.app.run(host='127.0.0.1', port={port}, debug=False)",
        ],
        cwd=PROJECT_ROOT,
        env=server_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        wait_for_http(f"http://127.0.0.1:{port}/api/status")
        yield {"base_url": f"http://127.0.0.1:{port}", "process": process}
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


@pytest.fixture
def db_connection(integration_environment):
    """Open a DB connection to the isolated integration database."""
    conn = connect(integration_environment["db_name"])
    try:
        yield conn
    finally:
        conn.close()
