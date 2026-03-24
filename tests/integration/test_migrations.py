"""Integration tests for SQL migrations."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from tests.integration.helpers import connect

BERLIN = ZoneInfo("Europe/Berlin")


def apply_sql_file(connection, path: Path):
    with connection.cursor() as cur:
        cur.execute(path.read_text())
    connection.commit()


@pytest.mark.integration
def test_timezone_fix_migration_is_idempotent(isolated_database):
    """The timezone correction migration should fix legacy rows exactly once."""
    migration_001 = Path("migrations/001_initial_schema.sql")
    migration_002 = Path("migrations/002_fix_train_data_timezone.sql")

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
