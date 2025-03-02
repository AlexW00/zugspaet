import json
import os
import shutil
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from config import DATA_DIR
from db_utils import (
    bulk_insert_train_data,
    get_db_connection,
    init_database,
    is_date_processed,
    mark_date_as_processed,
)


def get_plan_xml_rows(xml_path, alternative_station_names):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    station = root.get("station")
    if station in alternative_station_names:
        station = alternative_station_names[station]

    rows = []
    for s in root.findall("s"):
        s_id = s.get("id")
        train_type = s.find("tl").get("c") if s.find("tl") is not None else None
        train_number = s.find("tl").get("n") if s.find("tl") is not None else None
        ar_train_line_number = (
            s.find("ar").get("l") if s.find("ar") is not None else None
        )
        dp_train_line_number = (
            s.find("dp").get("l") if s.find("dp") is not None else None
        )

        if train_type in ["IC", "ICE", "EC"]:
            train_name = f"{train_type} {train_number}"
        else:
            if ar_train_line_number is not None:
                train_name = f"{train_type} {ar_train_line_number}"
            elif dp_train_line_number is not None:
                train_name = f"{train_type} {dp_train_line_number}"
            else:
                train_name = train_type

        s_id_split = s_id.split("-")

        dp_ppth = (
            s.find("dp").get("ppth") if s.find("dp") is not None else None
        )  # departure planed path
        if dp_ppth is None:
            final_destination_station = station
        else:
            final_destination_station = dp_ppth.split("|")[-1]

        rows.append(
            {
                "id": s_id,
                "station": station,
                "train_name": train_name,
                "final_destination_station": final_destination_station,
                "train_type": train_type,
                "arrival_planned_time": (
                    s.find("ar").get("pt") if s.find("ar") is not None else None
                ),
                "departure_planned_time": (
                    s.find("dp").get("pt") if s.find("dp") is not None else None
                ),
                "train_line_ride_id": "-".join(s_id_split[:-1]),
                "train_line_station_num": int(s_id_split[-1]),
            }
        )
    return rows


def get_plan_db(date_folders, alternative_station_names):
    rows = []

    for date_folder_path in tqdm(date_folders, desc="Processing plan files"):
        for xml_path in sorted(date_folder_path.iterdir()):
            if "plan" in xml_path.name:
                rows.extend(get_plan_xml_rows(xml_path, alternative_station_names))

    out_df = pd.DataFrame(rows)
    out_df["arrival_planned_time"] = pd.to_datetime(
        out_df["arrival_planned_time"], format="%y%m%d%H%M", errors="coerce"
    )
    out_df["departure_planned_time"] = pd.to_datetime(
        out_df["departure_planned_time"], format="%y%m%d%H%M", errors="coerce"
    )
    out_df = out_df.drop_duplicates()
    return out_df


def get_fchg_xml_rows(xml_path, id_to_data):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    for s in root.findall("s"):
        s_id = s.get("id")
        ar_ct = (
            s.find("ar").get("ct") if s.find("ar") is not None else None
        )  # arrival change
        dp_ct = (
            s.find("dp").get("ct") if s.find("dp") is not None else None
        )  # departure change
        ar_clt = (
            s.find("ar").get("clt") if s.find("ar") is not None else None
        )  # arrival cancellation time
        dp_clt = (
            s.find("dp").get("clt") if s.find("dp") is not None else None
        )  # departure cancellation time

        if ar_clt is None and dp_clt is None:
            is_canceled = False
        else:
            is_canceled = True

        if ar_ct is None and dp_ct is None and not is_canceled:
            continue

        # overwrite older data with new data
        id_to_data[s_id] = {
            "id": s_id,
            "arrival_change_time": ar_ct,
            "departure_change_time": dp_ct,
            "is_canceled": is_canceled,
        }


def get_fchg_db(date_folders):
    id_to_data = {}

    for date_folder_path in tqdm(date_folders, desc="Processing fchg files"):
        for xml_path in sorted(date_folder_path.iterdir()):
            if "fchg" in xml_path.name:
                get_fchg_xml_rows(xml_path, id_to_data)

    out_df = pd.DataFrame(id_to_data.values())
    out_df["arrival_change_time"] = pd.to_datetime(
        out_df["arrival_change_time"], format="%y%m%d%H%M", errors="coerce"
    )
    out_df["departure_change_time"] = pd.to_datetime(
        out_df["departure_change_time"], format="%y%m%d%H%M", errors="coerce"
    )
    out_df = out_df.drop_duplicates()
    return out_df


def delete_date_folder(date_folder):
    """Delete a date folder and all its contents if deletion is enabled."""
    should_delete = os.getenv("DELETE_XML_AFTER_IMPORT", "false").lower() == "true"
    if not should_delete:
        print(
            f"Skipping deletion of folder {date_folder} (deletion disabled by configuration)"
        )
        return

    try:
        shutil.rmtree(date_folder)
        print(f"Successfully deleted folder: {date_folder}")
    except Exception as e:
        print(f"Error deleting folder {date_folder}: {str(e)}")


def process_date_folder(date_folder, alternative_station_names, conn):
    """Process a single date folder and insert its data into the database."""
    date_str = date_folder.name

    if is_date_processed(conn, date_str):
        print(f"Date {date_str} has already been processed, skipping...")
        # Delete the folder since data is already in database
        delete_date_folder(date_folder)
        return

    print(f"Processing data for date: {date_str}")

    # Create a list with just this date folder
    date_folders = [date_folder]

    # Get the data for this date
    plan_df = get_plan_db(date_folders, alternative_station_names)
    fchg_df = get_fchg_db(date_folders)
    df = pd.merge(plan_df, fchg_df, on="id", how="left")

    # Apply the same transformations as before
    df["is_canceled"] = df["is_canceled"].astype("boolean").fillna(False)
    df["departure_change_time"] = df["departure_change_time"].fillna(
        df["departure_planned_time"]
    )
    df["arrival_change_time"] = df["arrival_change_time"].fillna(
        df["arrival_planned_time"]
    )

    departure_time_delta_in_min = (
        df["departure_change_time"] - df["departure_planned_time"]
    ).dt.total_seconds() / 60
    arrival_time_delta_in_min = (
        df["arrival_change_time"] - df["arrival_planned_time"]
    ).dt.total_seconds() / 60
    df["delay_in_min"] = departure_time_delta_in_min.fillna(arrival_time_delta_in_min)

    df["time"] = df["departure_change_time"].fillna(df["arrival_change_time"])

    df = df.drop("id", axis=1)

    df = df[
        [
            "station",
            "train_name",
            "final_destination_station",
            "delay_in_min",
            "time",
            "is_canceled",
            "train_type",
            "train_line_ride_id",
            "train_line_station_num",
            "arrival_planned_time",
            "arrival_change_time",
            "departure_planned_time",
            "departure_change_time",
        ]
    ].astype(
        {
            "station": "string",
            "train_name": "string",
            "final_destination_station": "string",
            "delay_in_min": "int32",
            "is_canceled": "boolean",
            "train_type": "string",
            "train_line_ride_id": "string",
            "train_line_station_num": "int32",
        }
    )

    # Insert the data into the database
    bulk_insert_train_data(conn, df)

    # Mark the date as processed
    mark_date_as_processed(conn, date_str)
    print(f"Successfully processed and stored data for {date_str}")

    # Delete the folder since data is now in database
    delete_date_folder(date_folder)


def import_data(
    xml_dir="/app/data/xml", alternative_station_names=None, specific_date=None
):
    """
    Main function to import data that can be called directly or via command line.

    Args:
        xml_dir (str, optional): Path to the directory where XML files are stored.
            If None, uses default path.
        alternative_station_names (dict, optional): Dict of alternative station names.
            If None, loads from json file.
        specific_date (str, optional): Specific date to process in YYYY-MM-DD format.
            If None, processes all unprocessed dates.

    Returns:
        list: List of processed date strings
    """
    processed_dates = []

    if not xml_dir.exists():
        raise FileNotFoundError(f"Data directory {xml_dir} does not exist")

    # Load alternative station names if not provided
    if alternative_station_names is None:
        alt_station_file = Path("alternative_station_name_to_station_name.json")
        if not alt_station_file.exists():
            raise FileNotFoundError(
                f"Alternative station names file {alt_station_file} does not exist"
            )
        with alt_station_file.open("r") as f:
            alternative_station_names = json.load(f)

    # Get database connection
    conn = get_db_connection()
    try:
        # If specific date is provided, only process that date
        if specific_date:
            date_folder = xml_dir / specific_date
            if not date_folder.exists():
                raise FileNotFoundError(
                    f"Data folder for date {specific_date} does not exist"
                )
            process_date_folder(date_folder, alternative_station_names, conn)
            processed_dates.append(specific_date)
        else:
            # Process all date folders that haven't been processed yet
            date_folders = sorted(
                [d for d in xml_dir.iterdir() if d.is_dir()],
                key=lambda x: datetime.strptime(x.name, "%Y-%m-%d"),
            )

            for date_folder in date_folders:
                try:
                    process_date_folder(date_folder, alternative_station_names, conn)
                    processed_dates.append(date_folder.name)
                except Exception as e:
                    print(f"Error processing {date_folder.name}: {str(e)}")
                    continue

    finally:
        conn.close()

    return processed_dates


if __name__ == "__main__":
    try:
        # If a date argument is provided, process only that date
        specific_date = sys.argv[1] if len(sys.argv) > 1 else None
        processed = import_data(specific_date=specific_date)
        print(f"Successfully processed dates: {', '.join(processed)}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
