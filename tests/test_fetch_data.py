"""Unit tests for fetch_data.py."""

from unittest.mock import patch

import pytest
import responses


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_rate_limiter_acquire(self):
        """Test acquiring a token from rate limiter."""
        from fetch_data import RateLimiter

        limiter = RateLimiter(rate=10, per=1)

        result = limiter.acquire()

        assert result is True
        assert limiter.tokens == 9

    def test_rate_limiter_multiple_acquires(self):
        """Test multiple token acquisitions."""
        from fetch_data import RateLimiter

        limiter = RateLimiter(rate=5, per=60)

        for _ in range(5):
            limiter.acquire()

        assert limiter.tokens == 0


class TestGetApiCredentials:
    """Tests for get_api_credentials function."""

    def test_get_api_credentials_success(self, monkeypatch):
        """Test getting credentials from environment."""
        from fetch_data import get_api_credentials

        monkeypatch.setenv("API_KEY", "my_api_key")
        monkeypatch.setenv("CLIENT_ID", "my_client_id")

        api_key, client_id = get_api_credentials()

        assert api_key == "my_api_key"
        assert client_id == "my_client_id"

    def test_get_api_credentials_missing_api_key(self, monkeypatch):
        """Test error when API_KEY is missing."""
        from fetch_data import get_api_credentials

        monkeypatch.delenv("API_KEY", raising=False)

        with pytest.raises(ValueError, match="No API Key provided"):
            get_api_credentials()

    def test_get_api_credentials_missing_client_id(self, monkeypatch):
        """Test error when CLIENT_ID is missing."""
        from fetch_data import get_api_credentials

        monkeypatch.setenv("API_KEY", "my_api_key")
        monkeypatch.delenv("CLIENT_ID", raising=False)

        with pytest.raises(ValueError, match="No Client Id provided"):
            get_api_credentials()


class TestGetApiHeaders:
    """Tests for get_api_headers function."""

    def test_get_api_headers(self):
        """Test header generation."""
        from fetch_data import get_api_headers

        headers = get_api_headers("test_key", "test_client")

        assert headers["DB-Api-Key"] == "test_key"
        assert headers["DB-Client-Id"] == "test_client"
        assert headers["accept"] == "application/xml"


class TestSaveApiData:
    """Tests for save_api_data function."""

    @responses.activate
    def test_save_api_data_success(self, tmp_path):
        """Test successful API data save."""
        from fetch_data import save_api_data

        url = "https://api.example.com/data"
        responses.add(
            responses.GET,
            url,
            body="<root><data>test</data></root>",
            status=200,
            content_type="application/xml",
        )

        save_path = tmp_path / "test.xml"
        headers = {"Authorization": "Bearer test"}

        # Reset the rate limiter for this test
        with patch("fetch_data.rate_limiter") as mock_limiter:
            mock_limiter.acquire.return_value = True
            save_api_data(url, save_path, headers, prettify=False)

        assert save_path.exists()
        content = save_path.read_text()
        assert "<data>test</data>" in content

    @responses.activate
    def test_save_api_data_retry_on_failure(self, tmp_path):
        """Test retry mechanism on failed request."""
        from fetch_data import save_api_data

        url = "https://api.example.com/data"
        # First request fails, second succeeds
        responses.add(responses.GET, url, body="Error", status=500)
        responses.add(
            responses.GET,
            url,
            body="<root><data>test</data></root>",
            status=200,
            content_type="application/xml",
        )

        save_path = tmp_path / "test.xml"
        headers = {"Authorization": "Bearer test"}

        with patch("fetch_data.rate_limiter") as mock_limiter:
            mock_limiter.acquire.return_value = True
            with patch("fetch_data.time.sleep"):  # Skip actual sleep
                save_api_data(url, save_path, headers, prettify=False, max_retries=2)

        assert save_path.exists()
