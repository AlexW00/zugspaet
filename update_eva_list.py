import logging
import os
import time
from pathlib import Path

import pandas as pd
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


def fetch_and_process_stations(api_key, client_id, eva_dir="/app/data/eva", categories="1-3", max_retries=5):
    # API configuration
    base_url = "https://apis.deutschebahn.com/db-api-marketplace/apis/station-data/v2/stations"
    headers = {
        "DB-Api-Key": api_key,
        "DB-Client-Id": client_id,
        "accept": "application/json",
    }

    all_stations = []
    offset = 0
    limit = 100

    while True:
        # Add query parameters
        params = {"category": categories, "offset": offset, "limit": limit}

        # Attempt API request with retries
        success = False
        for attempt in range(max_retries):
            try:
                response = requests.get(base_url, headers=headers, params=params, timeout=10)
                response.raise_for_status()

                if attempt > 0:
                    logger.info(f"Success after {attempt} attempts for offset {offset}.")

                success = True
                break
            except (RequestException, ConnectionError) as e:
                logger.error(f"Attempt {attempt + 1} failed for offset {offset}: {e}")
                if attempt < max_retries - 1:
                    logger.info("Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    logger.error(f"Failed to fetch data after {max_retries} attempts")
                    return False
            finally:
                time.sleep(1 / 60)  # Rate limiting

        if not success:
            return False

        # Process the JSON response
        json_data = response.json()
        results = json_data.get("result", [])

        if not results:
            break

        # Process station data
        for station in results:
            evas = []
            longitude = None
            latitude = None

            for eva in station.get("evaNumbers", []):
                evas.append(f"0{eva.get('number')}")  # add a leading 0 for the eva
                if eva.get("isMain"):
                    coords = eva.get("geographicCoordinates", {}).get("coordinates")
                    if coords:
                        longitude = coords[0]
                        latitude = coords[1]

            station_data = {
                "name": station.get("name"),
                "category": station.get("category"),
                "evas": ",".join(evas),
                "longitude": longitude,
                "latitude": latitude,
            }
            all_stations.append(station_data)

        logger.info(f"Fetched {len(results)} stations (offset {offset}). Total: {len(all_stations)}")

        offset += limit
        if len(results) < limit:
            break

    # Create DataFrame
    if not all_stations:
        logger.warning("No stations found.")
        return True  # Or False depending on whether empty result is failure

    df = pd.DataFrame(all_stations)
    df = df.sort_values("name", ascending=True)

    # Ensure data directory exists
    eva_dir = Path(eva_dir)
    eva_dir.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    output_file = eva_dir / "current_eva_list.csv"
    df.to_csv(
        output_file,
        index=False,
        quoting=2,
        quotechar='"',
    )
    logger.info(f"Successfully processed {len(df)} stations and saved to {output_file}")
    return True


def run_eva_list_update(api_key, client_id, eva_dir="/app/data/eva"):
    """Run the EVA list update process."""
    logger.info("Starting EVA list update process...")
    try:
        success = fetch_and_process_stations(api_key, client_id, eva_dir)
        if success:
            logger.info("EVA list update completed successfully")
        else:
            logger.error("EVA list update failed")
    except Exception as e:
        logger.error(f"Unexpected error during EVA list update process: {e!s}")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Get API credentials from environment variables
    api_key = os.getenv("API_KEY")
    client_id = os.getenv("CLIENT_ID")
    eva_dir = os.getenv("EVA_DIR", "data")

    if not api_key or not client_id:
        logger.error("Error: API_KEY and CLIENT_ID environment variables must be set")
        exit(1)

    # Run the update
    run_eva_list_update(api_key, client_id, eva_dir)
