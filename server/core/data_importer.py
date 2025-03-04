import json
import logging
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from server.config.settings import XML_DIR
from server.db.database import db_cursor

logger = logging.getLogger(__name__)


def parse_xml_file(xml_file):
    """Parse a single XML file and extract train data."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        train_data = []
        for timetable in root.findall(".//timetable"):
            station = timetable.get("station")
            if not station:
                continue

            for s in timetable.findall(".//s"):
                train_name = s.get("id", "")
                if not train_name:
                    continue

                # Extract arrival data
                ar = s.find("ar")
                if ar is not None:
                    delay = ar.get("ct_delay", "0")
                    try:
                        delay_minutes = int(delay)
                    except ValueError:
                        delay_minutes = 0

                    time_str = ar.get("pt", "")
                    if not time_str:
                        continue

                    try:
                        time = datetime.strptime(time_str, "%y%m%d%H%M")
                    except ValueError:
                        continue

                    final_destination = (
                        ar.get("ppth", "").split("|")[-1] if ar.get("ppth") else None
                    )
                    is_canceled = ar.get("c", "0") == "1"

                    train_data.append(
                        {
                            "station": station,
                            "train_name": train_name,
                            "time": time,
                            "delay_in_min": delay_minutes,
                            "final_destination_station": final_destination,
                            "is_canceled": is_canceled,
                        }
                    )

        return train_data
    except Exception as e:
        logger.error(f"Error parsing XML file {xml_file}: {str(e)}")
        return []


def import_data():
    """Import all XML files from the data directory into the database."""
    processed_dates = []

    # Get all XML files in the data directory
    xml_files = []
    for subdir in XML_DIR.iterdir():
        if subdir.is_dir():
            xml_files.extend(subdir.glob("*.xml"))

    if not xml_files:
        logger.warning("No XML files found to import")
        return []

    total_records = 0
    for xml_file in xml_files:
        try:
            train_data = parse_xml_file(xml_file)
            if not train_data:
                continue

            # Insert data into database
            with db_cursor() as cur:
                for record in train_data:
                    cur.execute(
                        """
                        INSERT INTO train_data 
                        (station, train_name, time, "delay_in_min", "final_destination_station", "is_canceled")
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                        (
                            record["station"],
                            record["train_name"],
                            record["time"],
                            record["delay_in_min"],
                            record["final_destination_station"],
                            record["is_canceled"],
                        ),
                    )

            date_str = xml_file.stem  # Get filename without extension
            processed_dates.append(date_str)
            total_records += len(train_data)
            logger.info(f"Imported {len(train_data)} records from {xml_file.name}")

        except Exception as e:
            logger.error(f"Error processing file {xml_file}: {str(e)}")
            continue

    logger.info(f"Total records imported: {total_records}")
    return processed_dates
