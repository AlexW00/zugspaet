import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import requests
from requests.exceptions import RequestException

from server.config.settings import API_KEY, CLIENT_ID, EVA_DIR, XML_DIR

logger = logging.getLogger(__name__)


def fetch_timetables(date_str, save_folder):
    """Fetch timetable data for a specific date."""
    url = (
        "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/plan/"
        + date_str
    )
    headers = {
        "DB-Client-Id": CLIENT_ID,
        "DB-Api-Key": API_KEY,
        "accept": "application/xml",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        save_path = save_folder / f"{date_str}.xml"
        save_path.write_bytes(response.content)
        logger.info(f"Successfully saved timetable data for {date_str}")
        return True
    except RequestException as e:
        logger.error(f"Failed to fetch timetable data for {date_str}: {str(e)}")
        return False


def fetch_data():
    """Fetch all required data from the Deutsche Bahn API."""
    current_date = datetime.now()
    dates_to_fetch = [
        (current_date + timedelta(days=i)).strftime("%y%m%d")
        for i in range(-1, 3)  # Fetch data for yesterday, today, and next 2 days
    ]

    # Create timestamp-based folder for this fetch
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_folder = XML_DIR / timestamp
    save_folder.mkdir(parents=True, exist_ok=True)

    success_count = 0
    for date_str in dates_to_fetch:
        if fetch_timetables(date_str, save_folder):
            success_count += 1

    if success_count == 0:
        logger.error("Failed to fetch any timetable data")
        return None

    logger.info(
        f"Successfully fetched {success_count} out of {len(dates_to_fetch)} timetables"
    )
    return save_folder


def fetch_eva_numbers():
    """Fetch the current list of EVA numbers (station identifiers)."""
    url = "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/station"
    headers = {
        "DB-Client-Id": CLIENT_ID,
        "DB-Api-Key": API_KEY,
        "accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Save the EVA numbers
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = EVA_DIR / f"eva_numbers_{timestamp}.json"

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=2)

        # Also save as current version
        current_path = EVA_DIR / "current_eva_list.json"
        with open(current_path, "w", encoding="utf-8") as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=2)

        logger.info("Successfully updated EVA numbers list")
        return True
    except RequestException as e:
        logger.error(f"Failed to fetch EVA numbers: {str(e)}")
        return False
