"""Unit tests for db_utils.py."""

from unittest.mock import MagicMock, patch

import pandas as pd
import psycopg2
import pytest


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
