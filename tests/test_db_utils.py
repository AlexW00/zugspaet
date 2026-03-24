"""Unit tests for db_utils.py."""

from unittest.mock import MagicMock, patch

import pandas as pd
import psycopg2
import pytest


class FakeMigrationCursor:
    """Tiny cursor fake for exercising migration tracking logic."""

    def __init__(self, state):
        self.state = state
        self._result_one = None
        self._result_all = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        normalized_sql = " ".join(sql.split())
        self.state["executed_sql"].append((normalized_sql, params))

        if normalized_sql.startswith("CREATE TABLE IF NOT EXISTS schema_migrations"):
            self._result_one = None
            self._result_all = None
            return

        if normalized_sql.startswith("SELECT to_regclass(%s)"):
            relation_name = params[0]
            self._result_one = (relation_name if relation_name in self.state["relations"] else None,)
            self._result_all = None
            return

        if normalized_sql.startswith("SELECT EXISTS(SELECT 1 FROM applied_data_fixes"):
            fix_name = params[0]
            self._result_one = (fix_name in self.state["data_fixes"],)
            self._result_all = None
            return

        if normalized_sql == "SELECT filename FROM schema_migrations":
            self._result_all = [(name,) for name in sorted(self.state["applied_migrations"])]
            self._result_one = None
            return

        if normalized_sql.startswith(
            "INSERT INTO schema_migrations (filename) VALUES (%s) ON CONFLICT (filename) DO NOTHING"
        ):
            self.state["applied_migrations"].add(params[0])
            self._result_one = None
            self._result_all = None
            return

        self.state["migration_sql"].append(normalized_sql)
        self._result_one = None
        self._result_all = None

    def fetchone(self):
        return self._result_one

    def fetchall(self):
        return self._result_all


class FakeMigrationConnection:
    """Connection fake that keeps migration-tracking state across init_database calls."""

    def __init__(self, state):
        self.state = state
        self.commit = MagicMock()
        self.rollback = MagicMock()
        self.close = MagicMock()

    def cursor(self):
        return FakeMigrationCursor(self.state)


class TestGetDbConnection:
    """Tests for get_db_connection function."""

    @patch("db_utils.psycopg2.connect")
    def test_get_db_connection_success(self, mock_connect):
        """Test successful database connection."""
        from db_utils import get_db_connection

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        result = get_db_connection()

        assert result == mock_conn
        mock_connect.assert_called_once()

    @patch("db_utils.time.sleep")
    @patch("db_utils.psycopg2.connect")
    def test_get_db_connection_retry_then_success(self, mock_connect, mock_sleep):
        """Test connection retry on failure then success."""
        from db_utils import get_db_connection

        mock_conn = MagicMock()
        mock_connect.side_effect = [psycopg2.Error("Connection failed"), mock_conn]

        result = get_db_connection(max_retries=3, retry_delay=1)

        assert result == mock_conn
        assert mock_connect.call_count == 2
        mock_sleep.assert_called_once_with(1)

    @patch("db_utils.time.sleep")
    @patch("db_utils.psycopg2.connect")
    def test_get_db_connection_all_retries_fail(self, mock_connect, mock_sleep):
        """Test connection failure after all retries."""
        from db_utils import get_db_connection

        mock_connect.side_effect = psycopg2.Error("Connection failed")

        with pytest.raises(Exception) as exc_info:
            get_db_connection(max_retries=3, retry_delay=1)

        assert "Failed to connect to database after 3 attempts" in str(exc_info.value)
        assert mock_connect.call_count == 3


class TestIsDateProcessed:
    """Tests for is_date_processed function."""

    def test_is_date_processed_true(self, mock_db_connection):
        """Test when date has been processed."""
        from db_utils import is_date_processed

        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = (True,)

        result = is_date_processed(mock_conn, "2024-01-01")

        assert result is True

    def test_is_date_processed_false(self, mock_db_connection):
        """Test when date has not been processed."""
        from db_utils import is_date_processed

        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = (False,)

        result = is_date_processed(mock_conn, "2024-01-01")

        assert result is False


class TestMarkDateAsProcessed:
    """Tests for mark_date_as_processed function."""

    def test_mark_date_as_processed(self, mock_db_connection):
        """Test marking a date as processed."""
        from db_utils import mark_date_as_processed

        mock_conn, _mock_cursor = mock_db_connection

        mark_date_as_processed(mock_conn, "2024-01-01")

        mock_conn.commit.assert_called_once()


class TestBulkInsertTrainData:
    """Tests for bulk_insert_train_data function."""

    def test_bulk_insert_empty_dataframe(self, mock_db_connection):
        """Test that empty dataframe does nothing."""
        from db_utils import bulk_insert_train_data

        mock_conn, mock_cursor = mock_db_connection
        empty_df = pd.DataFrame()

        bulk_insert_train_data(mock_conn, empty_df)

        mock_cursor.execute.assert_not_called()

    @patch("db_utils.execute_values")
    def test_bulk_insert_with_data(self, mock_execute_values, mock_db_connection):
        """Test bulk insert with valid data."""
        from db_utils import bulk_insert_train_data

        mock_conn, _mock_cursor = mock_db_connection
        df = pd.DataFrame(
            {
                "station": ["Berlin Hbf", "München Hbf"],
                "delay": [5, 10],
            }
        )

        bulk_insert_train_data(mock_conn, df)

        mock_execute_values.assert_called_once()
        mock_conn.commit.assert_called_once()


class TestInitDatabase:
    """Tests for migration tracking in init_database."""

    def test_init_database_records_and_skips_migrations_after_first_run(self, monkeypatch, tmp_path):
        """A migration file should execute once, then be skipped on later startups."""
        from db_utils import init_database

        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()
        (migrations_dir / "001_initial_schema.sql").write_text("SELECT 1 AS migration_001;")
        (migrations_dir / "002_fix_train_data_timezone.sql").write_text("SELECT 2 AS migration_002;")

        state = {
            "relations": set(),
            "data_fixes": set(),
            "applied_migrations": set(),
            "executed_sql": [],
            "migration_sql": [],
        }
        fake_conn = FakeMigrationConnection(state)

        monkeypatch.chdir(tmp_path)
        with patch("db_utils.get_db_connection", return_value=fake_conn):
            init_database()
            init_database()

        assert state["applied_migrations"] == {
            "001_initial_schema.sql",
            "002_fix_train_data_timezone.sql",
        }
        assert state["migration_sql"].count("SELECT 1 AS migration_001;") == 1
        assert state["migration_sql"].count("SELECT 2 AS migration_002;") == 1
        assert fake_conn.commit.call_count == 2

    def test_init_database_bootstraps_existing_migrations_without_rerunning_them(self, monkeypatch, tmp_path):
        """Older deployments should backfill migration history and skip already-applied SQL files."""
        from db_utils import init_database

        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()
        (migrations_dir / "001_initial_schema.sql").write_text("SELECT 1 AS migration_001;")
        (migrations_dir / "002_fix_train_data_timezone.sql").write_text("SELECT 2 AS migration_002;")

        state = {
            "relations": {
                "public.processed_dates",
                "public.train_data",
                "public.v_train_stations",
                "public.v_station_trains",
                "public.v_train_arrivals",
                "public.applied_data_fixes",
            },
            "data_fixes": {"fix_train_data_timezone_v1"},
            "applied_migrations": set(),
            "executed_sql": [],
            "migration_sql": [],
        }
        fake_conn = FakeMigrationConnection(state)

        monkeypatch.chdir(tmp_path)
        with patch("db_utils.get_db_connection", return_value=fake_conn):
            init_database()

        assert state["applied_migrations"] == {
            "001_initial_schema.sql",
            "002_fix_train_data_timezone.sql",
        }
        assert state["migration_sql"] == []
