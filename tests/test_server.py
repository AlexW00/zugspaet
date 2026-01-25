"""Unit tests for server.py."""

import sys
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def app_module(mock_env_vars):
    """Import and return the server module with side effects mocked."""
    with patch("db_utils.init_database"), \
         patch("apscheduler.schedulers.background.BackgroundScheduler") as mock_scheduler_cls, \
         patch("flask_limiter.Limiter"):
        
        # Mock the scheduler instance
        mock_scheduler = MagicMock()
        mock_scheduler_cls.return_value = mock_scheduler

        # Ensure we get a fresh import of server to run its top-level code with mocks
        if "server" in sys.modules:
            del sys.modules["server"]
        
        import server
        yield server


@pytest.fixture
def client(app_module):
    """Create a test client for the app."""
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client


class TestPublicEndpoints:
    """Tests for public API endpoints."""

    def test_train_stations(self, client, app_module):
        """Test retrieving all train stations."""
        with patch("server.get_all_stations") as mock_get_stations:
            mock_get_stations.return_value = ["Berlin Hbf", "München Hbf"]
            
            response = client.get("/api/trainStations")
            
            assert response.status_code == 200
            assert response.json == ["Berlin Hbf", "München Hbf"]

    def test_trains_success(self, client, app_module):
        """Test retrieving trains for a station."""
        with patch("server.validate_station_name") as mock_validate, \
             patch("server.get_trains_for_station") as mock_get_trains:
            
            mock_validate.return_value = True
            mock_get_trains.return_value = ["ICE 123", "RB 45"]
            
            response = client.get("/api/trains?trainStation=Berlin Hbf")
            
            assert response.status_code == 200
            assert response.json == ["ICE 123", "RB 45"]

    def test_trains_missing_param(self, client):
        """Test error when trainStation param is missing."""
        response = client.get("/api/trains")
        assert response.status_code == 400
        assert "trainStation parameter is required" in response.json["error"]

    def test_trains_invalid_station(self, client):
        """Test error when station name is invalid."""
        with patch("server.validate_station_name") as mock_validate:
            mock_validate.return_value = False
            
            response = client.get("/api/trains?trainStation=InvalidStation")
            
            assert response.status_code == 400
            assert "Invalid station name" in response.json["error"]

    def test_train_arrivals_success(self, client):
        """Test retrieving arrivals for a train."""
        with patch("server.validate_station_name") as mock_val_station, \
             patch("server.validate_train_name") as mock_val_train, \
             patch("server.get_train_arrivals") as mock_get_arrivals:
            
            mock_val_station.return_value = True
            mock_val_train.return_value = True
            mock_get_arrivals.return_value = [{"time": "10:00", "delayInMin": 5}]
            
            response = client.get("/api/trainArrivals?trainStation=Berlin Hbf&trainName=ICE 123")
            
            assert response.status_code == 200
            assert response.json == [{"time": "10:00", "delayInMin": 5}]

    def test_train_arrivals_missing_params(self, client):
        """Test error when parameters are missing."""
        # Missing trainName
        response = client.get("/api/trainArrivals?trainStation=Berlin Hbf")
        assert response.status_code == 400
        
        # Missing trainStation
        response = client.get("/api/trainArrivals?trainName=ICE 123")
        assert response.status_code == 400

    def test_system_status_success(self, client, app_module):
        """Test system status endpoint."""
        # Mock pathlib.Path.glob to return some dummy paths (folders)
        mock_path = MagicMock()
        mock_path.is_dir.return_value = True
        
        # We need to patch the global 'xml_dir' in the server module or where it's used
        # Since 'xml_dir' is imported/defined at top level, we mock the attribute on the module
        # Manually patch xml_dir on the module instance we have
        mock_xml_dir = MagicMock()
        mock_xml_dir.glob.return_value = [mock_path, mock_path]
        original_xml_dir = app_module.xml_dir
        app_module.xml_dir = mock_xml_dir
        
        try:

            # Mock database connection for processed dates
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            with patch("server.get_db_connection", return_value=mock_conn):
                response = client.get("/api/status")
                
                assert response.status_code == 200
                assert response.json["status"] == "ok"
                assert response.json["data_directory"]["num_date_folders"] == 2
        finally:
            app_module.xml_dir = original_xml_dir

    def test_last_import(self, client):
        """Test last import date endpoint."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Mock date object
        mock_date = MagicMock()
        mock_date.isoformat.return_value = "2024-01-01T23:30:00"
        mock_cursor.fetchone.return_value = [mock_date]
        
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch("server.get_db_connection", return_value=mock_conn):
            response = client.get("/api/lastImport")
            
            assert response.status_code == 200
            assert response.json["lastImport"] == "2024-01-01T23:30:00"


class TestPrivateEndpoints:
    """Tests for private API endpoints."""

    def test_trigger_fetch_unauthorized(self, client):
        """Test fetch without API key."""
        response = client.post("/private/api/fetch")
        assert response.status_code == 401

    def test_trigger_fetch_wrong_key(self, client):
        """Test fetch with wrong API key."""
        headers = {"X-Private-Api-Key": "wrong_key"}
        response = client.post("/private/api/fetch", headers=headers)
        assert response.status_code == 401

    def test_trigger_fetch_success(self, client):
        """Test successful fetch trigger."""
        headers = {"X-Private-Api-Key": "test_private_key"}
        
        with patch("server.fetch_data", return_value="/tmp/save_folder") as mock_fetch:
            response = client.post("/private/api/fetch", headers=headers)
            
            assert response.status_code == 200
            assert response.json["status"] == "success"
            mock_fetch.assert_called_once()

    def test_trigger_import_success(self, client):
        """Test successful import trigger."""
        headers = {"X-Private-Api-Key": "test_private_key"}
        
        with patch("server.import_data", return_value=["2024-01-01"]) as mock_import:
            response = client.post("/private/api/import", headers=headers)
            
            assert response.status_code == 200
            assert response.json["status"] == "success"
            mock_import.assert_called_once()


class TestHelpers:
    """Tests for helper functions in server.py."""
    
    def test_sanitize_input(self, app_module):
        """Test input sanitization."""
        sanitize = app_module.sanitize_input
        
        assert sanitize("test") == "test"
        assert sanitize("test<script>") == "test<script>"  # Current impl acts as simple filter or existence check?
        # Re-reading sanitize_input:
        # value = "".join(char for char in value if char.isprintable())
        # value[:max_length]
        
        assert sanitize("Hello\nWorld") == "HelloWorld" # \n is not printable? Let's check python
        # In Python, \n is printable? No, str.isprintable() is False for \n.
        
        assert sanitize(None) is None
