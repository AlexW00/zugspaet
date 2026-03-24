import time
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from config import DB_CONFIG

SCHEMA_MIGRATIONS_TABLE = "schema_migrations"


def get_db_connection(max_retries=5, retry_delay=1):
    """Create and return a database connection with retries."""
    last_exception = None
    for attempt in range(max_retries):
        try:
            return psycopg2.connect(**DB_CONFIG)
        except psycopg2.Error as e:
            last_exception = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            raise Exception(f"Failed to connect to database after {max_retries} attempts: {last_exception!s}")


def _ensure_schema_migrations_table(cur):
    """Create the migration ledger table when it does not exist yet."""
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA_MIGRATIONS_TABLE} (
            filename VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _relation_exists(cur, relation_name):
    """Return whether a relation already exists in the public schema."""
    cur.execute("SELECT to_regclass(%s)", (relation_name,))
    return cur.fetchone()[0] is not None


def _legacy_initial_schema_exists(cur):
    """Detect databases where the original schema was already created before tracking existed."""
    required_relations = (
        "public.processed_dates",
        "public.train_data",
        "public.v_train_stations",
        "public.v_station_trains",
        "public.v_train_arrivals",
    )
    return all(_relation_exists(cur, relation_name) for relation_name in required_relations)


def _legacy_timezone_fix_exists(cur):
    """Detect whether the timezone data-fix migration already completed on an older deployment."""
    if not _relation_exists(cur, "public.applied_data_fixes"):
        return False

    cur.execute(
        "SELECT EXISTS(SELECT 1 FROM applied_data_fixes WHERE name = %s)",
        ("fix_train_data_timezone_v1",),
    )
    return cur.fetchone()[0]


def _record_migration(cur, filename):
    """Persist the migration filename so future startups can skip it."""
    cur.execute(
        f"""
        INSERT INTO {SCHEMA_MIGRATIONS_TABLE} (filename)
        VALUES (%s)
        ON CONFLICT (filename) DO NOTHING
        """,
        (filename,),
    )


def _bootstrap_previously_applied_migrations(cur):
    """Backfill migration history for deployments that predate schema_migrations."""
    if _legacy_initial_schema_exists(cur):
        _record_migration(cur, "001_initial_schema.sql")

    if _legacy_timezone_fix_exists(cur):
        _record_migration(cur, "002_fix_train_data_timezone.sql")


def _get_applied_migrations(cur):
    """Return the set of migration filenames that already ran."""
    cur.execute(f"SELECT filename FROM {SCHEMA_MIGRATIONS_TABLE}")
    return {row[0] for row in cur.fetchall()}


def init_database():
    """Initialize the database by running all migrations."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            _ensure_schema_migrations_table(cur)
            _bootstrap_previously_applied_migrations(cur)

            # Get all migration files
            migrations_dir = Path("migrations")
            migration_files = sorted(migrations_dir.glob("*.sql"))
            applied_migrations = _get_applied_migrations(cur)

            for migration_file in migration_files:
                if migration_file.name in applied_migrations:
                    print(f"Skipping migration: {migration_file.name}")
                    continue

                print(f"Applying migration: {migration_file.name}")
                with open(migration_file) as f:
                    migration_sql = f.read()
                    cur.execute(migration_sql)
                _record_migration(cur, migration_file.name)
                applied_migrations.add(migration_file.name)
        conn.commit()
        print("Database initialization completed successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def is_date_processed(conn, date_str):
    """Check if a specific date has already been processed."""
    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS(SELECT 1 FROM processed_dates WHERE date = %s)", (date_str,))
        return cur.fetchone()[0]


def mark_date_as_processed(conn, date_str):
    """Mark a date as processed in the database."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO processed_dates (date) VALUES (%s) ON CONFLICT (date) DO NOTHING",
            (date_str,),
        )
    conn.commit()


def bulk_insert_train_data(conn, data_df):
    """Insert a DataFrame of train data into the database."""
    if data_df.empty:
        return

    # Create a copy to avoid modifying the original DataFrame
    df_to_insert = data_df.copy()

    # Convert all numeric columns to native Python types
    numeric_columns = df_to_insert.select_dtypes(include=["int32", "int64", "float32", "float64"]).columns
    for col in numeric_columns:
        df_to_insert[col] = df_to_insert[col].astype(float).astype(object)

    # Convert DataFrame to list of tuples, ensuring native Python types
    values = [tuple(None if pd.isna(x) else x for x in row) for row in df_to_insert.values]

    # Generate the column names string
    columns = df_to_insert.columns.tolist()

    with conn.cursor() as cur:
        # Use execute_values for efficient bulk insertion
        execute_values(
            cur,
            f"""
            INSERT INTO train_data (
                {", ".join(columns)}
            ) VALUES %s
            """,
            values,
            page_size=1000,
        )
    conn.commit()
