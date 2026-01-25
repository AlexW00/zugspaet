"""Shared pytest fixtures for zugspaet backend tests."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PASSWORD", "test_password")
    monkeypatch.setenv("POSTGRES_DB", "test_db")
    monkeypatch.setenv("API_KEY", "test_api_key")
    monkeypatch.setenv("CLIENT_ID", "test_client_id")
    monkeypatch.setenv("PRIVATE_API_KEY", "test_private_key")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("DATA_DIR", "/tmp/test_data")
    monkeypatch.setenv("XML_DIR", "/tmp/test_xml")
    monkeypatch.setenv("EVA_DIR", "/tmp/test_eva")


@pytest.fixture
def mock_db_connection():
    """Create a mock database connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return mock_conn, mock_cursor


@pytest.fixture
def sample_train_data():
    """Sample train data for testing."""
    return {
        "station": "Berlin Hbf",
        "train_name": "ICE 123",
        "scheduled_arrival": "2024-01-01 10:00:00",
        "actual_arrival": "2024-01-01 10:05:00",
        "delay_minutes": 5,
    }
