import os
import time
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from config import DB_CONFIG


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
            raise Exception(
                f"Failed to connect to database after {max_retries} attempts: {str(last_exception)}"
            )


def init_database():
    """Initialize the database by running all migrations."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Get all migration files
            migrations_dir = Path("migrations")
            migration_files = sorted(migrations_dir.glob("*.sql"))

            for migration_file in migration_files:
                print(f"Applying migration: {migration_file.name}")
                with open(migration_file, "r") as f:
                    migration_sql = f.read()
                    cur.execute(migration_sql)
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
        cur.execute(
            "SELECT EXISTS(SELECT 1 FROM processed_dates WHERE date = %s)", (date_str,)
        )
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
    numeric_columns = df_to_insert.select_dtypes(
        include=["int32", "int64", "float32", "float64"]
    ).columns
    for col in numeric_columns:
        df_to_insert[col] = df_to_insert[col].astype(float).astype(object)

    # Convert DataFrame to list of tuples, ensuring native Python types
    values = [
        tuple(None if pd.isna(x) else x for x in row) for row in df_to_insert.values
    ]

    # Generate the column names string
    columns = df_to_insert.columns.tolist()

    with conn.cursor() as cur:
        # Use execute_values for efficient bulk insertion
        execute_values(
            cur,
            f"""
            INSERT INTO train_data (
                {', '.join(columns)}
            ) VALUES %s
            """,
            values,
            page_size=1000,
        )
    conn.commit()
