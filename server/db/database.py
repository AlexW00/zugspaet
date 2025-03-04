import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

from server.config.settings import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


def get_db_connection():
    """Create a database connection."""
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


@contextmanager
def db_cursor(cursor_factory=None):
    """Context manager for database cursor."""
    conn = get_db_connection()
    try:
        if cursor_factory:
            cursor = conn.cursor(cursor_factory=cursor_factory)
        else:
            cursor = conn.cursor()
        yield cursor
        conn.commit()
    finally:
        conn.close()


def init_database():
    """Initialize the database schema using migration files."""
    with db_cursor() as cur:
        # Read and execute the migration file
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "migrations",
            "001_initial_schema.sql",
        )
        with open(migration_path, "r") as f:
            migration_sql = f.read()
            cur.execute(migration_sql)


def get_all_stations():
    """Retrieve all unique station names."""
    with db_cursor(psycopg2.extras.DictCursor) as cur:
        cur.execute(
            """
            SELECT DISTINCT station 
            FROM train_data 
            ORDER BY station
        """
        )
        return [row["station"] for row in cur.fetchall()]


def get_trains_for_station(station, days_cutoff=30):
    """Get all trains for a specific station."""
    with db_cursor(psycopg2.extras.DictCursor) as cur:
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
        return [row["train_name"] for row in cur.fetchall()]


def get_train_arrivals(station, train_name, days_cutoff=30):
    """Get arrival data for a specific train at a station."""
    with db_cursor(psycopg2.extras.DictCursor) as cur:
        cur.execute(
            """
            SELECT 
                delay_in_min,
                time,
                final_destination_station,
                is_canceled
            FROM train_data 
            WHERE station = %s 
            AND train_name = %s 
            AND time >= CURRENT_DATE - interval '%s days'
            ORDER BY time DESC
        """,
            (station, train_name, days_cutoff),
        )
        return [dict(row) for row in cur.fetchall()]


def validate_station_name(station):
    """Check if a station exists in the database."""
    with db_cursor() as cur:
        cur.execute(
            "SELECT EXISTS(SELECT 1 FROM train_data WHERE station = %s LIMIT 1)",
            (station,),
        )
        return cur.fetchone()[0]


def validate_train_name(train_name, station):
    """Check if a train exists for a given station."""
    with db_cursor() as cur:
        cur.execute(
            "SELECT EXISTS(SELECT 1 FROM train_data WHERE station = %s AND train_name = %s LIMIT 1)",
            (station, train_name),
        )
        return cur.fetchone()[0]


def get_filtered_arrivals(station=None, train_name=None, days_cutoff=30):
    """Get arrival data with optional station and train filters."""
    with db_cursor(psycopg2.extras.DictCursor) as cur:
        query = """
            SELECT 
                delay_in_min,
                time,
                final_destination_station,
                is_canceled,
                station,
                train_name
            FROM train_data 
            WHERE time >= CURRENT_DATE - interval '%s days'
        """
        params = [days_cutoff]

        if station:
            query += " AND station = %s"
            params.append(station)
        if train_name:
            query += " AND train_name = %s"
            params.append(train_name)

        query += " ORDER BY time DESC"
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


def get_train_suggestions(station=None):
    """Get train suggestions, optionally filtered by station."""
    with db_cursor(psycopg2.extras.DictCursor) as cur:
        query = """
            SELECT DISTINCT train_name 
            FROM train_data 
            WHERE time >= CURRENT_DATE - interval '30 days'
        """
        params = []

        if station:
            query += " AND station = %s"
            params.append(station)

        query += " ORDER BY train_name"
        cur.execute(query, params)
        return [row["train_name"] for row in cur.fetchall()]


def get_station_suggestions(train_name=None):
    """Get station suggestions, optionally filtered by train."""
    with db_cursor(psycopg2.extras.DictCursor) as cur:
        query = """
            SELECT DISTINCT station 
            FROM train_data 
            WHERE time >= CURRENT_DATE - interval '30 days'
        """
        params = []

        if train_name:
            query += " AND train_name = %s"
            params.append(train_name)

        query += " ORDER BY station"
        cur.execute(query, params)
        return [row["station"] for row in cur.fetchall()]
