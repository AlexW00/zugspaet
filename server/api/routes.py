import logging
from contextlib import contextmanager
from functools import wraps

import psycopg2.extras
from flask import Blueprint, jsonify, request, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from server.config.settings import PRIVATE_API_KEY, RATE_LIMITS
from server.core.data_fetcher import fetch_data, fetch_eva_numbers
from server.core.data_importer import import_data
from server.db.database import (
    db_cursor,
    get_all_stations,
    get_db_connection,
    get_filtered_arrivals,
    get_station_suggestions,
    get_train_suggestions,
    validate_station_name,
    validate_train_name,
)
from server.utils.helpers import sanitize_input

logger = logging.getLogger(__name__)

# Create Blueprint for API routes
api = Blueprint("api", __name__)

# Configure rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=RATE_LIMITS["default"])


def require_private_api_key(f):
    """Decorator to require private API key for protected endpoints."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("X-Private-Api-Key")
        if not auth_header or auth_header != PRIVATE_API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return decorated_function


@api.route("/train_stations", methods=["GET"])
def train_stations():
    """Get all train stations."""
    try:
        stations = get_all_stations()
        return jsonify(stations)
    except Exception as e:
        logger.error(f"Error fetching train stations: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@api.route("/trains", methods=["GET"])
def trains():
    """Get all trains, optionally filtered by station."""
    station = sanitize_input(request.args.get("train_station"))

    try:
        if station and not validate_station_name(station):
            return jsonify({"error": "Invalid station name"}), 400

        trains_list = get_train_suggestions(station)
        return jsonify(trains_list)
    except Exception as e:
        logger.error(f"Error fetching trains: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@api.route("/stations", methods=["GET"])
def stations():
    """Get all stations, optionally filtered by train."""
    train_name = sanitize_input(request.args.get("train_name"))

    try:
        stations_list = get_station_suggestions(train_name)
        return jsonify(stations_list)
    except Exception as e:
        logger.error(f"Error fetching stations: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@api.route("/arrivals", methods=["GET"])
def arrivals():
    """Get arrival data with optional station and train filters."""
    station = sanitize_input(request.args.get("train_station"))
    train_name = sanitize_input(request.args.get("train_name"))

    try:
        if station and not validate_station_name(station):
            return jsonify({"error": "Invalid station name"}), 400

        if train_name and station and not validate_train_name(train_name, station):
            return jsonify({"error": "Invalid train name for this station"}), 400

        arrivals = get_filtered_arrivals(station, train_name)
        return jsonify(arrivals)
    except Exception as e:
        logger.error(f"Error fetching arrivals: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@api.route("/status")
def system_status():
    """Get system status information."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get latest data timestamp
            cur.execute(
                """
                SELECT MAX(time) as latest_data,
                       COUNT(*) as total_records,
                       COUNT(DISTINCT station) as station_count,
                       COUNT(DISTINCT train_name) as train_count
                FROM train_data
            """
            )
            status = dict(cur.fetchone())

            # Get import statistics
            cur.execute(
                """
                SELECT COUNT(*) as today_records
                FROM train_data
                WHERE DATE(created_at) = CURRENT_DATE
            """
            )
            status.update(cur.fetchone())

        conn.close()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error fetching system status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@api.route("/private/api/fetch", methods=["POST"])
@require_private_api_key
def trigger_fetch():
    """Manually trigger data fetch."""
    try:
        save_folder = fetch_data()
        if save_folder:
            return jsonify({"message": f"Data fetch completed. Saved to {save_folder}"})
        return jsonify({"error": "Data fetch failed"}), 500
    except Exception as e:
        logger.error(f"Error during manual data fetch: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@api.route("/private/api/import", methods=["POST"])
@require_private_api_key
def trigger_import():
    """Manually trigger data import."""
    try:
        processed_dates = import_data()
        return jsonify(
            {"message": "Import completed", "processed_dates": processed_dates}
        )
    except Exception as e:
        logger.error(f"Error during manual data import: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@api.route("/last_import", methods=["GET"])
def last_import():
    """Get information about the last import."""
    try:
        with db_cursor(psycopg2.extras.DictCursor) as cur:
            cur.execute(
                """
                SELECT 
                    MAX(created_at) as last_import,
                    COUNT(*) as records_imported
                FROM train_data 
                """
            )
            result = dict(cur.fetchone())
            return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching last import info: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@api.route("/stats/delays", methods=["GET"])
def delay_statistics():
    """Get delay statistics for visualization."""
    station = sanitize_input(request.args.get("train_station"))
    train_name = sanitize_input(request.args.get("train_name"))
    days = int(sanitize_input(request.args.get("days", "30")))

    try:
        with db_cursor(psycopg2.extras.DictCursor) as cur:
            query = """
                SELECT 
                    ROUND(AVG(delay_in_min)) as avg_delay,
                    MIN(delay_in_min) as min_delay,
                    MAX(delay_in_min) as max_delay,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delay_in_min) as median_delay,
                    COUNT(*) as total_arrivals,
                    COUNT(CASE WHEN delay_in_min > 0 THEN 1 END) as delayed_arrivals,
                    COUNT(CASE WHEN delay_in_min <= 0 THEN 1 END) as ontime_arrivals
                FROM train_data
                WHERE NOT is_canceled
                AND time >= CURRENT_DATE - INTERVAL '%s days'
            """
            params = [days]

            if station:
                query += " AND station = %s"
                params.append(station)
            if train_name:
                query += " AND train_name = %s"
                params.append(train_name)

            cur.execute(query, params)
            result = dict(cur.fetchone())
            return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching delay statistics: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@api.route("/stats/delays/by_time", methods=["GET"])
def delays_by_time():
    """Get delay statistics grouped by time periods."""
    station = sanitize_input(request.args.get("train_station"))
    train_name = sanitize_input(request.args.get("train_name"))
    group_by = sanitize_input(request.args.get("group_by", "day"))  # hour, day, month
    days = int(sanitize_input(request.args.get("days", "30")))

    try:
        with db_cursor(psycopg2.extras.DictCursor) as cur:
            time_group = {
                "hour": "EXTRACT(HOUR FROM time)",
                "day": "EXTRACT(DOW FROM time)",
                "month": "EXTRACT(MONTH FROM time)",
            }.get(group_by, "EXTRACT(HOUR FROM time)")

            query = f"""
                SELECT 
                    {time_group} as time_group,
                    ROUND(AVG(delay_in_min)) as avg_delay,
                    COUNT(*) as total_arrivals,
                    COUNT(CASE WHEN delay_in_min > 0 THEN 1 END) as delayed_arrivals
                FROM train_data
                WHERE NOT is_canceled
                AND time >= CURRENT_DATE - INTERVAL '%s days'
            """
            params = [days]

            if station:
                query += " AND station = %s"
                params.append(station)
            if train_name:
                query += " AND train_name = %s"
                params.append(train_name)

            query += " GROUP BY time_group ORDER BY time_group"

            cur.execute(query, params)
            results = [dict(row) for row in cur.fetchall()]
            return jsonify(results)
    except Exception as e:
        logger.error(f"Error fetching time-based delay statistics: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@api.route("/stats/top_delays", methods=["GET"])
def top_delays():
    """Get top delayed stations or trains."""
    type_filter = sanitize_input(
        request.args.get("type", "station")
    )  # station or train
    limit = min(int(request.args.get("limit", 10)), 50)  # Cap at 50 results
    days = int(sanitize_input(request.args.get("days", "30")))

    try:
        with db_cursor(psycopg2.extras.DictCursor) as cur:
            group_by = "station" if type_filter == "station" else "train_name"

            query = f"""
                SELECT 
                    {group_by} as name,
                    ROUND(AVG(delay_in_min)) as avg_delay,
                    COUNT(*) as total_arrivals,
                    COUNT(CASE WHEN delay_in_min > 0 THEN 1 END) as delayed_arrivals,
                    ROUND(COUNT(CASE WHEN delay_in_min > 0 THEN 1 END)::float / COUNT(*) * 100, 2) as delay_percentage
                FROM train_data
                WHERE NOT is_canceled
                AND time >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY {group_by}
                HAVING COUNT(*) >= 10  -- Minimum sample size
                ORDER BY avg_delay DESC
                LIMIT %s
            """

            cur.execute(query, [days, limit])
            results = [dict(row) for row in cur.fetchall()]
            return jsonify(results)
    except Exception as e:
        logger.error(f"Error fetching top delays: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# Error handlers
@api.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors."""
    return jsonify({"error": "Rate limit exceeded"}), 429


@api.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500
