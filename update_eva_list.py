import logging
import os
import time
from pathlib import Path

import pandas as pd
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


def fetch_and_process_stations(
    api_key, client_id, eva_dir="/app/data/eva", categories="1-2", max_retries=5
):
    # API configuration
    base_url = (
        "https://apis.deutschebahn.com/db-api-marketplace/apis/station-data/v2/stations"
    )
    headers = {
        "DB-Api-Key": api_key,
        "DB-Client-Id": client_id,
        "accept": "application/json",
    }

    # Add query parameters
    params = {"category": categories}

    # Attempt API request with retries
    for attempt in range(max_retries):
        try:
            response = requests.get(
                base_url, headers=headers, params=params, timeout=10
            )
            response.raise_for_status()

            if attempt > 0:
                logger.info(f"Success after {attempt} attempts.")

            # Process the JSON response
            json_data = response.json()

            # Process station data
            stations = []
            for station in json_data["result"]:
                evas = []
                longitude = None
                latitude = None

                for eva in station["evaNumbers"]:
                    evas.append(f"0{eva.get('number')}")  # add a leading 0 for the eva
                    if eva.get("isMain"):
                        coords = eva["geographicCoordinates"]["coordinates"]
                        longitude = coords[0]
                        latitude = coords[1]

                station_data = {
                    "name": station.get("name"),
                    "category": station.get("category"),
                    "evas": ",".join(evas),
                    "longitude": longitude,
                    "latitude": latitude,
                }
                stations.append(station_data)

            # Create DataFrame
            df = pd.DataFrame(stations)
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
            logger.info(
                f"Successfully processed {len(df)} stations and saved to {output_file}"
            )
            return True

        except (RequestException, ConnectionError) as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                logger.info("Retrying in 2 seconds...")
                time.sleep(2)
            else:
                logger.error(f"Failed to fetch data after {max_retries} attempts")
                return False

        finally:
            time.sleep(1 / 60)  # Rate limiting

    return False


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
        logger.error(f"Unexpected error during EVA list update process: {str(e)}")


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
