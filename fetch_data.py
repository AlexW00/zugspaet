import os
import time
from datetime import datetime
from pathlib import Path
from threading import Lock
from time import time as current_time
from xml.dom.minidom import parseString

import pandas as pd
import requests
from requests.exceptions import RequestException


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, rate=50, per=60):
        self.rate = rate  # Number of tokens per time period
        self.per = per  # Time period in seconds
        self.tokens = rate  # Current token count
        self.last_update = current_time()
        self.lock = Lock()

    def _add_tokens(self):
        """Add tokens based on time elapsed."""
        now = current_time()
        time_passed = now - self.last_update
        new_tokens = time_passed * (self.rate / self.per)
        self.tokens = min(self.rate, self.tokens + new_tokens)
        self.last_update = now

    def acquire(self):
        """Acquire a token, waiting if necessary."""
        with self.lock:
            while self.tokens < 1:
                self._add_tokens()
                if self.tokens < 1:
                    time.sleep(0.1)  # Sleep briefly to prevent busy waiting

            self.tokens -= 1
            return True


# Create a global rate limiter instance
rate_limiter = RateLimiter(rate=50, per=60)  # 50 requests per minute


def get_api_credentials():
    """Get API credentials from environment variables."""
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("No API Key provided!")

    client_id = os.getenv("CLIENT_ID")
    if not client_id:
        raise ValueError("No Client Id provided!")

    return api_key, client_id


def get_api_headers(api_key, client_id):
    """Get API headers for requests."""
    return {
        "DB-Api-Key": api_key,
        "DB-Client-Id": client_id,
        "accept": "application/xml",
    }


def save_api_data(formatted_url, save_path, headers, prettify=True, max_retries=4, skip_if_exists=False):
    """Save API data to file with retries and rate limiting.

    Args:
        formatted_url: The API URL to fetch.
        save_path: Path to save the response.
        headers: HTTP headers for the request.
        prettify: Whether to prettify the XML output.
        max_retries: Number of retry attempts.
        skip_if_exists: If True, skip fetching if save_path already exists.
    """
    if skip_if_exists and save_path.exists():
        print(f"SKIPPED (exists): {save_path.name}")
        return

    for attempt in range(max_retries):
        try:
            # Acquire a token before making the request
            rate_limiter.acquire()

            response = requests.get(formatted_url, headers=headers, timeout=10)
            response.raise_for_status()
            if attempt > 0:
                print(f"Success after {attempt} attempts.")

            with save_path.open("w") as f:
                if prettify:
                    f.write(parseString(response.content).toprettyxml())
                else:
                    f.write(parseString(response.content).toxml())

            print("SUCCESS:", formatted_url)
            return  # Success, exit the function

        except (RequestException, ConnectionError) as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print("Retrying in 1 seconds...")
                time.sleep(1)
            else:
                print(f"Failed to fetch data after {max_retries} attempts: {formatted_url}")

    print(f"error: Could not retrieve data for {formatted_url}")


def fetch_data(
    api_key=None,
    client_id=None,
    eva_file="current_eva_list.csv",
    xml_dir="/app/data/xml",
    eva_dir="/app/data/eva",
):
    """
    Main function to fetch data that can be called directly or via command line.

    Args:
        api_key (str, optional): DB API key. If None, will try to get from environment.
        client_id (str, optional): DB Client ID. If None, will try to get from environment.
        eva_file (str): Path to the CSV file containing EVA numbers.
        xml_dir (str): Path to the directory where XML files will be saved.
        eva_dir (str): Path to the directory where EVA files will be saved.
    """
    if api_key is None or client_id is None:
        api_key, client_id = get_api_credentials()

    headers = get_api_headers(api_key, client_id)

    plan_url = "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/plan/{eva}/{date}/{hour}"
    fchg_url = "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/fchg/{eva}"

    date_str = datetime.now().strftime("%Y-%m-%d")
    date_str_url = date_str.replace("-", "")[2:]

    save_folder = Path(xml_dir) / date_str
    save_folder.mkdir(exist_ok=True, parents=True)

    df = pd.read_csv(Path(eva_dir) / eva_file)
    eva_list = []
    for evas in df["evas"]:
        eva_list.extend(evas.split(","))

    curent_hour = datetime.now().hour
    for eva in eva_list:
        formatted_fchg_url = fchg_url.format(eva=eva)
        save_api_data(
            formatted_fchg_url,
            save_folder / f"{eva}_fchg_{curent_hour:02}.xml",
            headers=headers,
            prettify=False,
        )

    print("curent_hour:", curent_hour)
    for eva in eva_list:
        for hour in range(curent_hour, curent_hour + 6):  # fetch this hour and the next 5 hours
            hour = hour % 24
            formatted_plan_url = plan_url.format(eva=eva, date=date_str_url, hour=f"{hour:02}")
            save_api_data(
                formatted_plan_url,
                save_folder / f"{eva}_plan_{hour:02}.xml",
                headers=headers,
                skip_if_exists=True,
            )

    print("Done")
    return save_folder


if __name__ == "__main__":
    fetch_data()
