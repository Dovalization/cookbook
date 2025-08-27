"""
Unit tests for HTTP client with retry logic and error handling.

Tests the HTTP client wrapper without making actual network requests.
"""

import pytest
import requests
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from shared.llm.http_client import HttpClient
from shared.errors import LLMError, LLMRateLimit, LLMAuthError


class TestHttpClient:
    """Test suite for HttpClient functionality."""

    @pytest.fixture
    def mock_session(self) -> Mock:
        """Create a mock requests session."""
        return Mock(spec=requests.Session)

    @pytest.fixture
    def http_client(self, mock_session: Mock) -> HttpClient:
        """Create HttpClient with mocked session."""
        return HttpClient(session=mock_session, timeout_s=30, max_retries=2)

    def test_initialization_with_defaults(self) -> None:
        """Test HttpClient initialization with default parameters."""
        client = HttpClient()
        
        assert isinstance(client.session, requests.Session)
        assert client.timeout_s == 60  # Default timeout
        assert client.max_retries == 3  # Default retries

    def test_initialization_with_custom_params(self, mock_session: Mock) -> None:
        """Test HttpClient initialization with custom parameters."""
        client = HttpClient(
            session=mock_session, 
            timeout_s=45, 
            max_retries=5
        )
        
        assert client.session is mock_session
        assert client.timeout_s == 45
        assert client.max_retries == 5

    def test_post_success(self, http_client: HttpClient, mock_session: Mock) -> None:
        """Test successful POST request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_session.post.return_value = mock_response

        url = "https://api.example.com/test"
        headers = {"Content-Type": "application/json"}
        json_data = {"key": "value"}

        result = http_client.post(url, headers=headers, json=json_data)

        assert result == {"result": "success"}
        mock_session.post.assert_called_once_with(
            url, 
            headers=headers, 
            json=json_data, 
            timeout=30
        )
        mock_response.raise_for_status.assert_called_once()

    def test_post_rate_limit_error(self, http_client: HttpClient, mock_session: Mock) -> None:
        """Test POST request with 429 rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_session.post.return_value = mock_response

        with pytest.raises(LLMRateLimit, match="Rate limited or timeout: 429"):
            http_client.post("https://api.example.com/test")

    def test_post_timeout_error(self, http_client: HttpClient, mock_session: Mock) -> None:
        """Test POST request with 408 timeout error."""
        mock_response = Mock()
        mock_response.status_code = 408
        mock_response.text = "Request timeout"
        mock_session.post.return_value = mock_response

        with pytest.raises(LLMRateLimit, match="Rate limited or timeout: 408"):
            http_client.post("https://api.example.com/test")

    def test_post_auth_error_401(self, http_client: HttpClient, mock_session: Mock) -> None:
        """Test POST request with 401 authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_session.post.return_value = mock_response

        with pytest.raises(LLMAuthError, match="Auth failed: Unauthorized"):
            http_client.post("https://api.example.com/test")

    def test_post_auth_error_403(self, http_client: HttpClient, mock_session: Mock) -> None:
        """Test POST request with 403 forbidden error."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_session.post.return_value = mock_response

        with pytest.raises(LLMAuthError, match="Auth failed: Forbidden"):
            http_client.post("https://api.example.com/test")

    def test_post_server_error_500(self, http_client: HttpClient, mock_session: Mock) -> None:
        """Test POST request with 500 server error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_session.post.return_value = mock_response

        with pytest.raises(LLMError, match="Server error 500: Internal server error"):
            http_client.post("https://api.example.com/test")

    def test_post_server_error_502(self, http_client: HttpClient, mock_session: Mock) -> None:
        """Test POST request with 502 bad gateway error."""
        mock_response = Mock()
        mock_response.status_code = 502
        mock_response.text = "Bad gateway"
        mock_session.post.return_value = mock_response

        with pytest.raises(LLMError, match="Server error 502: Bad gateway"):
            http_client.post("https://api.example.com/test")

    def test_post_other_http_error(self, http_client: HttpClient, mock_session: Mock) -> None:
        """Test POST request with other HTTP error that raises_for_status."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.HTTPError("Bad request")
        mock_session.post.return_value = mock_response

        with pytest.raises(LLMError, match="POST.*failed after 2 attempts"):
            http_client.post("https://api.example.com/test")

    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_post_retry_logic_success_on_second_attempt(
        self, 
        mock_sleep: Mock,
        http_client: HttpClient, 
        mock_session: Mock
    ) -> None:
        """Test retry logic succeeds on second attempt."""
        # First call fails, second succeeds
        error_response = Mock()
        error_response.status_code = 500
        error_response.text = "Server error"
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"result": "success"}
        
        mock_session.post.side_effect = [error_response, success_response]

        result = http_client.post("https://api.example.com/test")

        assert result == {"result": "success"}
        assert mock_session.post.call_count == 2
        mock_sleep.assert_called_once_with(1.0)  # First retry delay

    @patch('time.sleep')
    def test_post_retry_exhausted(
        self, 
        mock_sleep: Mock,
        http_client: HttpClient, 
        mock_session: Mock
    ) -> None:
        """Test retry logic exhausted after max attempts."""
        # All attempts fail
        error_response = Mock()
        error_response.status_code = 500
        error_response.text = "Server error"
        mock_session.post.return_value = error_response

        with pytest.raises(LLMError, match="POST.*failed after 2 attempts"):
            http_client.post("https://api.example.com/test")

        assert mock_session.post.call_count == 2  # max_retries = 2
        assert mock_sleep.call_count == 1  # One retry, one sleep

    @patch('time.sleep')
    def test_post_exponential_backoff(
        self, 
        mock_sleep: Mock,
        mock_session: Mock
    ) -> None:
        """Test exponential backoff in retry delays."""
        # Create client with more retries to test backoff
        http_client = HttpClient(session=mock_session, max_retries=4)
        
        error_response = Mock()
        error_response.status_code = 500
        error_response.text = "Server error"
        mock_session.post.return_value = error_response

        with pytest.raises(LLMError):
            http_client.post("https://api.example.com/test")

        # Check exponential backoff: 1.0, 2.0, 4.0
        expected_delays = [1.0, 2.0, 4.0]
        actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert actual_delays == expected_delays

    @patch('time.sleep')
    def test_post_backoff_cap(
        self, 
        mock_sleep: Mock,
        mock_session: Mock
    ) -> None:
        """Test that backoff delay is capped at 8 seconds."""
        # Create client with many retries to test cap
        http_client = HttpClient(session=mock_session, max_retries=6)
        
        error_response = Mock()
        error_response.status_code = 500
        error_response.text = "Server error"
        mock_session.post.return_value = error_response

        with pytest.raises(LLMError):
            http_client.post("https://api.example.com/test")

        # Check delays: 1.0, 2.0, 4.0, 8.0, 8.0 (capped at 8.0)
        expected_delays = [1.0, 2.0, 4.0, 8.0, 8.0]
        actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert actual_delays == expected_delays

    def test_post_connection_error(self, http_client: HttpClient, mock_session: Mock) -> None:
        """Test POST request with connection error."""
        mock_session.post.side_effect = requests.ConnectionError("Connection failed")

        with pytest.raises(LLMError, match="POST.*failed after 2 attempts.*Connection failed"):
            http_client.post("https://api.example.com/test")

    def test_post_request_exception(self, http_client: HttpClient, mock_session: Mock) -> None:
        """Test POST request with generic requests exception."""
        mock_session.post.side_effect = requests.RequestException("Request failed")

        with pytest.raises(LLMError, match="POST.*failed after 2 attempts.*Request failed"):
            http_client.post("https://api.example.com/test")

    def test_post_json_decode_error(self, http_client: HttpClient, mock_session: Mock) -> None:
        """Test POST request with JSON decode error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.return_value = None
        mock_session.post.return_value = mock_response

        with pytest.raises(LLMError, match="POST.*failed after 2 attempts"):
            http_client.post("https://api.example.com/test")

    def test_post_no_headers_or_json(self, http_client: HttpClient, mock_session: Mock) -> None:
        """Test POST request without headers or JSON data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_session.post.return_value = mock_response

        result = http_client.post("https://api.example.com/test")

        assert result == {"result": "success"}
        mock_session.post.assert_called_once_with(
            "https://api.example.com/test",
            headers=None,
            json=None,
            timeout=30
        )

    def test_post_long_error_text_truncation(
        self, 
        http_client: HttpClient, 
        mock_session: Mock
    ) -> None:
        """Test that long error text is truncated."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "x" * 300  # Long error message
        mock_session.post.return_value = mock_response

        with pytest.raises(LLMError) as exc_info:
            http_client.post("https://api.example.com/test")

        # Error message should contain truncated text (200 chars)
        error_message = str(exc_info.value)
        assert "x" * 200 in error_message
        assert len([part for part in error_message.split() if "x" in part][0]) <= 200

    @patch('time.sleep')
    def test_post_no_retry_on_auth_errors(
        self, 
        mock_sleep: Mock,
        http_client: HttpClient, 
        mock_session: Mock
    ) -> None:
        """Test that auth errors (401/403) are not retried."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_session.post.return_value = mock_response

        with pytest.raises(LLMAuthError):
            http_client.post("https://api.example.com/test")

        # Should only be called once, no retries
        assert mock_session.post.call_count == 1
        mock_sleep.assert_not_called()

    @patch('time.sleep')
    def test_post_no_retry_on_rate_limit(
        self, 
        mock_sleep: Mock,
        http_client: HttpClient, 
        mock_session: Mock
    ) -> None:
        """Test that rate limit errors (429) are not retried."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limited"
        mock_session.post.return_value = mock_response

        with pytest.raises(LLMRateLimit):
            http_client.post("https://api.example.com/test")

        # Should only be called once, no retries
        assert mock_session.post.call_count == 1
        mock_sleep.assert_not_called()