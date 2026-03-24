"""Live end-to-end integration test for fetch, import, and API serialization."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg2.extras
import pytest
import requests

BERLIN = ZoneInfo("Europe/Berlin")


@pytest.mark.integration
@pytest.mark.live_api
def test_live_fetch_import_and_api_serialization(
    integration_environment,
    live_api_credentials,
    boeblingen_eva_file,
    db_connection,
    started_server,
):
    """Fetch live Böblingen data, import it, then verify API output is Berlin-local."""
    import fetch_data
    import import_data_to_postgres

    save_folder = fetch_data.fetch_data(
        api_key=live_api_credentials["api_key"],
        client_id=live_api_credentials["client_id"],
        eva_file=Path(boeblingen_eva_file).name,
        xml_dir=integration_environment["xml_dir"],
        eva_dir=integration_environment["eva_dir"],
    )

    processed = import_data_to_postgres.import_data(
        xml_dir=integration_environment["xml_dir"],
        specific_date=Path(save_folder).name,
    )

    assert processed == [Path(save_folder).name]

    with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(
            """
            SELECT train_name, time
            FROM train_data
            WHERE station = %s
            ORDER BY time DESC
            LIMIT 1
            """,
            ("Böblingen",),
        )
        latest_row = cur.fetchone()

    assert latest_row is not None

    trains_response = requests.get(
        f"{started_server['base_url']}/api/trains",
        params={"trainStation": "Böblingen"},
        timeout=10,
    )
    trains_response.raise_for_status()
    train_names = trains_response.json()

    assert latest_row["train_name"] in train_names

    arrivals_response = requests.get(
        f"{started_server['base_url']}/api/trainArrivals",
        params={"trainStation": "Böblingen", "trainName": latest_row["train_name"]},
        timeout=10,
    )
    arrivals_response.raise_for_status()
    arrivals = arrivals_response.json()

    assert arrivals
    assert arrivals[0]["time"] == latest_row["time"].astimezone(BERLIN).isoformat()

    last_import_response = requests.get(f"{started_server['base_url']}/api/lastImport", timeout=10)
    last_import_response.raise_for_status()
    last_import = last_import_response.json()["lastImport"]

    assert last_import is not None
    assert datetime.fromisoformat(last_import).tzinfo is not None
