"""Integration tests for SQL migrations."""

import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from tests.integration.helpers import PROJECT_ROOT, connect, reload_module

BERLIN = ZoneInfo("Europe/Berlin")


def apply_sql_file(connection, path: Path):
    with connection.cursor() as cur:
        cur.execute(path.read_text())
    connection.commit()


def load_db_utils_for_test_database(monkeypatch, isolated_database):
    """Reload db_utils so init_database() points at the isolated Postgres database."""
    monkeypatch.chdir(PROJECT_ROOT)
    monkeypatch.setenv("DB_HOST", os.getenv("DB_HOST", "127.0.0.1"))
    monkeypatch.setenv("DB_PORT", os.getenv("DB_PORT", "5432"))
    monkeypatch.setenv("DB_NAME", isolated_database)
    monkeypatch.setenv("DB_USER", os.getenv("DB_USER", "postgres"))
    monkeypatch.setenv(
        "DB_PASSWORD",
        os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", ""),
    )
    monkeypatch.setenv("DB_OPTIONS", "-c timezone=Europe/Berlin")

    reload_module("config")
    return reload_module("db_utils")


@pytest.mark.integration
def test_timezone_fix_migration_is_idempotent(isolated_database):
    """The timezone correction migration should fix legacy rows exactly once."""
    migration_001 = PROJECT_ROOT / "migrations/001_initial_schema.sql"
    migration_002 = PROJECT_ROOT / "migrations/002_fix_train_data_timezone.sql"

    with connect(isolated_database) as conn:
        apply_sql_file(conn, migration_001)

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO train_data (
                    station,
                    train_name,
                    final_destination_station,
                    delay_in_min,
                    time,
                    is_canceled,
                    train_type,
                    train_line_ride_id,
                    train_line_station_num,
                    arrival_planned_time,
                    arrival_change_time,
                    departure_planned_time,
                    departure_change_time
                ) VALUES (
                    'Böblingen',
                    'IC 281',
                    'Stuttgart Hbf',
                    0,
                    TIMESTAMPTZ '2026-03-24 16:50:00+00',
                    FALSE,
                    'IC',
                    'probe-ride',
                    1,
                    TIMESTAMPTZ '2026-03-24 16:45:00+00',
                    TIMESTAMPTZ '2026-03-24 16:45:00+00',
                    TIMESTAMPTZ '2026-03-24 16:50:00+00',
                    TIMESTAMPTZ '2026-03-24 16:50:00+00'
                )
                """
            )
        conn.commit()

        apply_sql_file(conn, migration_002)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    time,
                    departure_planned_time,
                    departure_change_time
                FROM train_data
                WHERE train_line_ride_id = 'probe-ride'
                """
            )
            first_run = cur.fetchone()
            cur.execute("SELECT COUNT(*) FROM applied_data_fixes WHERE name = 'fix_train_data_timezone_v1'")
            marker_count = cur.fetchone()[0]

        apply_sql_file(conn, migration_002)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    time,
                    departure_planned_time,
                    departure_change_time
                FROM train_data
                WHERE train_line_ride_id = 'probe-ride'
                """
            )
            second_run = cur.fetchone()

    expected = (
        datetime(2026, 3, 24, 16, 50, tzinfo=BERLIN),
        datetime(2026, 3, 24, 16, 50, tzinfo=BERLIN),
        datetime(2026, 3, 24, 16, 50, tzinfo=BERLIN),
    )

    assert first_run == expected
    assert second_run == expected
    assert marker_count == 1


@pytest.mark.integration
def test_init_database_tracks_and_skips_applied_migrations(monkeypatch, isolated_database, capsys):
    """Running init_database twice should apply migrations once and skip them later."""
    db_utils = load_db_utils_for_test_database(monkeypatch, isolated_database)

    db_utils.init_database()
    first_output = capsys.readouterr().out

    db_utils.init_database()
    second_output = capsys.readouterr().out

    with connect(isolated_database) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT filename FROM schema_migrations ORDER BY filename")
            applied = [row[0] for row in cur.fetchall()]

    assert applied == [
        "001_initial_schema.sql",
        "002_fix_train_data_timezone.sql",
    ]
    assert "Applying migration: 001_initial_schema.sql" in first_output
    assert "Applying migration: 002_fix_train_data_timezone.sql" in first_output
    assert "Skipping migration: 001_initial_schema.sql" in second_output
    assert "Skipping migration: 002_fix_train_data_timezone.sql" in second_output


@pytest.mark.integration
def test_init_database_bootstraps_legacy_deployments(monkeypatch, isolated_database, capsys):
    """Older databases without schema_migrations should be backfilled instead of rerun."""
    migration_001 = PROJECT_ROOT / "migrations/001_initial_schema.sql"
    migration_002 = PROJECT_ROOT / "migrations/002_fix_train_data_timezone.sql"

    with connect(isolated_database) as conn:
        apply_sql_file(conn, migration_001)
        apply_sql_file(conn, migration_002)

    db_utils = load_db_utils_for_test_database(monkeypatch, isolated_database)
    db_utils.init_database()
    output = capsys.readouterr().out

    with connect(isolated_database) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT filename FROM schema_migrations ORDER BY filename")
            applied = [row[0] for row in cur.fetchall()]

    assert applied == [
        "001_initial_schema.sql",
        "002_fix_train_data_timezone.sql",
    ]
    assert "Applying migration: 001_initial_schema.sql" not in output
    assert "Applying migration: 002_fix_train_data_timezone.sql" not in output
    assert "Skipping migration: 001_initial_schema.sql" in output
    assert "Skipping migration: 002_fix_train_data_timezone.sql" in output
