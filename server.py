import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import psycopg2.extras
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from db_utils import get_db_connection
from fetch_data import fetch_data
from import_data_to_postgres import import_data

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)
# Create file handler
file_handler = RotatingFileHandler("logs/app.log", maxBytes=10240, backupCount=10)
file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
    )
)
file_handler.setLevel(logging.INFO)

# Load environment variables from .env file

api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("No API Key provided!")

client_id = os.getenv("CLIENT_ID")
if not client_id:
    raise ValueError("No Client Id provided!")


def run_data_fetch():
    """Run the data fetch process."""
    app.logger.info("Starting scheduled data fetch process...")

    try:
        app.logger.info("Fetching new data...")
        save_folder = fetch_data(api_key=api_key, client_id=client_id)
        app.logger.info(
            f"Data fetch completed successfully. Data saved to {save_folder}"
        )

    except Exception as e:
        app.logger.error(f"Unexpected error during data fetch process: {str(e)}")


def run_data_import():
    """Run the data import process."""
    app.logger.info("Starting scheduled import process...")

    try:
        app.logger.info("Importing data to database...")
        processed_dates = import_data()
        if processed_dates:
            app.logger.info(
                f"Successfully processed dates: {', '.join(processed_dates)}"
            )
        else:
            app.logger.info("No new dates to process")

    except Exception as e:
        app.logger.error(f"Unexpected error during data import process: {str(e)}")


app = Flask(__name__, static_folder="frontend/dist", static_url_path="")
# Configure CORS
CORS(
    app, resources={r"/api/*": {"origins": "*"}}
)  # In production, replace * with specific origins

# Add file handler to Flask logger
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["20000 per day", "1000 per hour"],
)


def sanitize_input(value, max_length=500):
    """Basic input sanitization."""
    if value is None:
        return None
    # Remove any non-printable characters
    value = "".join(char for char in value if char.isprintable())
    # Limit length
    return value[:max_length]


def validate_station_name(station):
    """Validate station name exists in database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT EXISTS(SELECT 1 FROM train_data WHERE station = %s LIMIT 1)",
                (station,),
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


def validate_train_name(train_name, station):
    """Validate train name exists for given station."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT EXISTS(SELECT 1 FROM train_data WHERE station = %s AND train_name = %s LIMIT 1)",
                (station, train_name),
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


def get_all_stations():
    """Retrieve all unique station names from the database."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                """
                SELECT DISTINCT station 
                FROM train_data 
                ORDER BY station
            """
            )
            stations = [row["station"] for row in cur.fetchall()]
            return stations
    finally:
        conn.close()


def get_trains_for_station(station, days_cutoff=30):
    """Retrieve all unique train names for a given station within the date cutoff period."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                """
                SELECT DISTINCT train_name 
                FROM train_data 
                WHERE station = %s 
                AND time >= CURRENT_DATE - interval '%s days'
                ORDER BY train_name
            """,
                (station, days_cutoff),
            )
            trains = [row["train_name"] for row in cur.fetchall()]
            return trains
    finally:
        conn.close()


def get_train_arrivals(station, train_name, days_cutoff=30):
    """Retrieve all arrivals for a specific train at a specific station within the date cutoff period."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                """
                SELECT 
                    delay_in_min as "delayInMin",
                    time,
                    final_destination_station as "finalDestinationStation",
                    is_canceled as "isCanceled"
                FROM train_data 
                WHERE station = %s 
                AND train_name = %s 
                AND time >= CURRENT_DATE - interval '%s days'
                ORDER BY time DESC
            """,
                (station, train_name, days_cutoff),
            )
            arrivals = [dict(row) for row in cur.fetchall()]
            return arrivals
    finally:
        conn.close()


@app.route("/api/trainStations", methods=["GET"])
def train_stations():
    try:
        stations = get_all_stations()
        return jsonify(stations)
    except Exception as e:
        app.logger.error(f"Error in train_stations: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/trains", methods=["GET"])
def trains():
    station = sanitize_input(request.args.get("trainStation"))
    if not station:
        return jsonify({"error": "trainStation parameter is required"}), 400

    # Get and validate days_cutoff parameter
    try:
        days_cutoff = int(request.args.get("dateCutoff", 30))
        if days_cutoff < 1:
            return jsonify({"error": "dateCutoff must be a positive integer"}), 400
    except ValueError:
        return jsonify({"error": "dateCutoff must be a valid integer"}), 400

    # Validate station exists
    if not validate_station_name(station):
        return jsonify({"error": "Invalid station name"}), 400

    try:
        trains = get_trains_for_station(station, days_cutoff)
        return jsonify(trains)
    except Exception as e:
        app.logger.error(f"Error in trains: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/trainArrivals", methods=["GET"])
def train_arrivals():
    station = sanitize_input(request.args.get("trainStation"))
    train_name = sanitize_input(request.args.get("trainName"))

    if not station or not train_name:
        return (
            jsonify(
                {"error": "Both trainStation and trainName parameters are required"}
            ),
            400,
        )

    # Get and validate days_cutoff parameter
    try:
        days_cutoff = int(request.args.get("dateCutoff", 30))
        if days_cutoff < 1:
            return jsonify({"error": "dateCutoff must be a positive integer"}), 400
    except ValueError:
        return jsonify({"error": "dateCutoff must be a valid integer"}), 400

    # Validate inputs
    if not validate_station_name(station):
        return jsonify({"error": "Invalid station name"}), 400

    if not validate_train_name(train_name, station):
        return jsonify({"error": "Invalid train name for this station"}), 400

    try:
        arrivals = get_train_arrivals(station, train_name, days_cutoff)
        return jsonify(arrivals)
    except Exception as e:
        app.logger.error(f"Error in train_arrivals: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# Error handlers
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded"}), 429


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


# Serve static files from the frontend/dist directory
@app.route("/")
def serve_frontend():
    return send_from_directory(app.static_folder, "index.html")


# Catch-all route to handle SPA routing
@app.route("/<path:path>")
def catch_all(path):
    # First try to serve as a static file
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    # If not a static file, return index.html for client-side routing
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    # Verify static folder exists
    if not os.path.exists(app.static_folder):
        print(f"Warning: Static folder {app.static_folder} does not exist!")
        os.makedirs(app.static_folder, exist_ok=True)

    # Initialize and start the scheduler
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        run_data_fetch,
        trigger=CronTrigger(minute="*/1"),
        id="daily_data_fetch",
        name="Daily Data Fetch",
    )

    scheduler.add_job(
        run_data_import,
        trigger=CronTrigger(hour=3, minute=0),  # Run at 3:00 AM every day
        id="daily_data_import",
        name="Daily Data Import",
    )

    scheduler.start()

    app.run(
        host="0.0.0.0",
        port=5000,
    )  # Enable HTTPS in production
