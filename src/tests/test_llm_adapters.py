"""
Unit tests for LLM adapters with mocked HTTP responses.

Tests provider-specific implementations without making actual API calls.
"""

import pytest
from unittest.mock import Mock
from typing import List

from shared.llm.adapters import (
    OpenAIAdapter, 
    AnthropicAdapter, 
    OllamaAdapter, 
    LLMResult, 
    BaseAdapter
)
from shared.llm.config import LLMConfig
from shared.llm.http_client import HttpClient
from shared.core.types import ChatMessage
from shared.errors import LLMError, LLMAuthError


class TestBaseAdapter:
    """Test suite for BaseAdapter utilities."""

    def test_require_success(self) -> None:
        """Test require method with valid value."""
        result = BaseAdapter.require("valid-value", "TEST_VAR")
        assert result == "valid-value"

    def test_require_none_raises_auth_error(self) -> None:
        """Test require method with None raises auth error."""
        with pytest.raises(LLMAuthError, match="Missing TEST_VAR"):
            BaseAdapter.require(None, "TEST_VAR")

    def test_require_empty_string_raises_auth_error(self) -> None:
        """Test require method with empty string raises auth error."""
        with pytest.raises(LLMAuthError, match="Missing TEST_VAR"):
            BaseAdapter.require("", "TEST_VAR")

    def test_ensure_dict_success(self) -> None:
        """Test ensure_dict with valid dictionary."""
        test_dict = {"key": "value"}
        result = BaseAdapter.ensure_dict(test_dict, "test_provider")
        assert result == test_dict

    def test_ensure_dict_invalid_type_raises_error(self) -> None:
        """Test ensure_dict with non-dictionary raises error."""
        with pytest.raises(LLMError, match="test_provider: expected JSON object"):
            BaseAdapter.ensure_dict("not a dict", "test_provider")

    def test_split_system_message_no_system(self) -> None:
        """Test split_system_message with no system messages."""
        messages: List[ChatMessage] = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        
        system, core = BaseAdapter.split_system_message(messages)
        
        assert system is None
        assert core == messages

    def test_split_system_message_with_system_first(self) -> None:
        """Test split_system_message with system message first."""
        messages: List[ChatMessage] = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        
        system, core = BaseAdapter.split_system_message(messages)
        
        assert system == "You are helpful"
        assert len(core) == 2
        assert core[0]["role"] == "user"
        assert core[1]["role"] == "assistant"

    def test_split_system_message_multiple_systems(self) -> None:
        """Test split_system_message with multiple system messages (takes first)."""
        messages: List[ChatMessage] = [
            {"role": "system", "content": "First system"},
            {"role": "user", "content": "Hello"},
            {"role": "system", "content": "Second system"},
        ]
        
        system, core = BaseAdapter.split_system_message(messages)
        
        assert system == "First system"
        assert len(core) == 2
        assert core[0]["role"] == "user"
        assert core[1]["role"] == "system"
        assert core[1]["content"] == "Second system"


class TestOpenAIAdapter:
    """Test suite for OpenAI adapter."""

    @pytest.fixture
    def config(self) -> LLMConfig:
        """Create test config for OpenAI."""
        return LLMConfig(
            provider="openai",
            model="gpt-4",
            temperature=0.7,
            max_tokens=150,
            openai_api_key="test-openai-key"
        )

    @pytest.fixture
    def mock_http_client(self) -> Mock:
        """Create mock HTTP client."""
        mock_client = Mock(spec=HttpClient)
        return mock_client

    @pytest.fixture
    def adapter(self) -> OpenAIAdapter:
        """Create OpenAI adapter instance."""
        return OpenAIAdapter()

    def test_chat_success(
        self, 
        adapter: OpenAIAdapter, 
        config: LLMConfig, 
        mock_http_client: Mock
    ) -> None:
        """Test successful OpenAI chat request."""
        # Mock successful response
        mock_response = {
            "choices": [{
                "message": {"content": "Hello! How can I help you?"}
            }],
            "model": "gpt-4",
            "usage": {"prompt_tokens": 10, "completion_tokens": 8}
        }
        mock_http_client.post.return_value = mock_response

        messages: List[ChatMessage] = [
            {"role": "user", "content": "Hello"}
        ]

        result = adapter.chat(config, messages, mock_http_client)

        # Verify result
        assert isinstance(result, LLMResult)
        assert result.text == "Hello! How can I help you?"
        assert result.provider == "openai"
        assert result.model == "gpt-4"
        assert result.usage == {"prompt_tokens": 10, "completion_tokens": 8}

        # Verify HTTP call
        mock_http_client.post.assert_called_once_with(
            config.openai_url(),
            headers={
                "Authorization": "Bearer test-openai-key",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 150
            }
        )

    def test_chat_no_max_tokens(
        self, 
        adapter: OpenAIAdapter, 
        mock_http_client: Mock
    ) -> None:
        """Test OpenAI chat without max_tokens parameter."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            max_tokens=None,  # No max tokens
            openai_api_key="test-key"
        )

        mock_response = {
            "choices": [{"message": {"content": "Response"}}]
        }
        mock_http_client.post.return_value = mock_response

        adapter.chat(config, [{"role": "user", "content": "test"}], mock_http_client)

        # Verify max_tokens is not in payload
        call_kwargs = mock_http_client.post.call_args.kwargs
        payload = call_kwargs["json"]
        assert "max_tokens" not in payload

    def test_chat_missing_api_key(
        self, 
        adapter: OpenAIAdapter, 
        mock_http_client: Mock
    ) -> None:
        """Test OpenAI chat with missing API key."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            openai_api_key=None  # Missing key
        )

        with pytest.raises(LLMAuthError, match="Missing OPENAI_API_KEY"):
            adapter.chat(config, [{"role": "user", "content": "test"}], mock_http_client)

    def test_chat_malformed_response(
        self, 
        adapter: OpenAIAdapter, 
        config: LLMConfig, 
        mock_http_client: Mock
    ) -> None:
        """Test OpenAI chat with malformed response."""
        # Response missing expected structure
        mock_response = {"error": "Invalid request"}
        mock_http_client.post.return_value = mock_response

        with pytest.raises(LLMError, match="OpenAI: unexpected response format"):
            adapter.chat(config, [{"role": "user", "content": "test"}], mock_http_client)


class TestAnthropicAdapter:
    """Test suite for Anthropic adapter."""

    @pytest.fixture
    def config(self) -> LLMConfig:
        """Create test config for Anthropic."""
        return LLMConfig(
            provider="anthropic",
            model="claude-3-sonnet-20240229",
            temperature=0.5,
            max_tokens=200,
            anthropic_api_key="test-anthropic-key",
            anthropic_version="2023-06-01"
        )

    @pytest.fixture
    def mock_http_client(self) -> Mock:
        """Create mock HTTP client."""
        return Mock(spec=HttpClient)

    @pytest.fixture
    def adapter(self) -> AnthropicAdapter:
        """Create Anthropic adapter instance."""
        return AnthropicAdapter()

    def test_chat_success(
        self, 
        adapter: AnthropicAdapter, 
        config: LLMConfig, 
        mock_http_client: Mock
    ) -> None:
        """Test successful Anthropic chat request."""
        mock_response = {
            "content": [
                {"type": "text", "text": "Hello! I'm Claude."}
            ],
            "model": "claude-3-sonnet-20240229",
            "usage": {"input_tokens": 15, "output_tokens": 12}
        }
        mock_http_client.post.return_value = mock_response

        messages: List[ChatMessage] = [
            {"role": "user", "content": "Hello"}
        ]

        result = adapter.chat(config, messages, mock_http_client)

        assert result.text == "Hello! I'm Claude."
        assert result.provider == "anthropic"
        assert result.model == "claude-3-sonnet-20240229"

        # Verify headers
        call_kwargs = mock_http_client.post.call_args.kwargs
        headers = call_kwargs["headers"]
        assert headers["x-api-key"] == "test-anthropic-key"
        assert headers["anthropic-version"] == "2023-06-01"

    def test_chat_with_system_message(
        self, 
        adapter: AnthropicAdapter, 
        config: LLMConfig, 
        mock_http_client: Mock
    ) -> None:
        """Test Anthropic chat with system message."""
        mock_response = {
            "content": [{"type": "text", "text": "I am helpful."}]
        }
        mock_http_client.post.return_value = mock_response

        messages: List[ChatMessage] = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"}
        ]

        adapter.chat(config, messages, mock_http_client)

        # Verify system message is in payload, not in messages
        call_kwargs = mock_http_client.post.call_args.kwargs
        payload = call_kwargs["json"]
        
        assert payload["system"] == "You are a helpful assistant."
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["role"] == "user"

    def test_chat_message_format_conversion(
        self, 
        adapter: AnthropicAdapter, 
        config: LLMConfig, 
        mock_http_client: Mock
    ) -> None:
        """Test Anthropic message format conversion."""
        mock_response = {
            "content": [{"type": "text", "text": "Response"}]
        }
        mock_http_client.post.return_value = mock_response

        messages: List[ChatMessage] = [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Answer"},
        ]

        adapter.chat(config, messages, mock_http_client)

        call_kwargs = mock_http_client.post.call_args.kwargs
        anthropic_messages = call_kwargs["json"]["messages"]

        # Verify format conversion
        assert len(anthropic_messages) == 2
        assert anthropic_messages[0]["role"] == "user"
        assert anthropic_messages[0]["content"] == [{"type": "text", "text": "Question"}]
        assert anthropic_messages[1]["role"] == "assistant"
        assert anthropic_messages[1]["content"] == [{"type": "text", "text": "Answer"}]

    def test_chat_multiple_content_blocks(
        self, 
        adapter: AnthropicAdapter, 
        config: LLMConfig, 
        mock_http_client: Mock
    ) -> None:
        """Test Anthropic response with multiple content blocks."""
        mock_response = {
            "content": [
                {"type": "text", "text": "First part. "},
                {"type": "text", "text": "Second part."}
            ]
        }
        mock_http_client.post.return_value = mock_response

        result = adapter.chat(config, [{"role": "user", "content": "test"}], mock_http_client)

        assert result.text == "First part. Second part."

    def test_chat_missing_api_key(
        self, 
        adapter: AnthropicAdapter, 
        mock_http_client: Mock
    ) -> None:
        """Test Anthropic chat with missing API key."""
        config = LLMConfig(
            provider="anthropic",
            model="claude-3-sonnet-20240229",
            anthropic_api_key=None
        )

        with pytest.raises(LLMAuthError, match="Missing ANTHROPIC_API_KEY"):
            adapter.chat(config, [{"role": "user", "content": "test"}], mock_http_client)

    def test_chat_malformed_response(
        self, 
        adapter: AnthropicAdapter, 
        config: LLMConfig, 
        mock_http_client: Mock
    ) -> None:
        """Test Anthropic chat with malformed response."""
        mock_response = {"content": "not a list"}
        mock_http_client.post.return_value = mock_response

        with pytest.raises(LLMError, match="Anthropic: unexpected response format"):
            adapter.chat(config, [{"role": "user", "content": "test"}], mock_http_client)


class TestOllamaAdapter:
    """Test suite for Ollama adapter."""

    @pytest.fixture
    def config(self) -> LLMConfig:
        """Create test config for Ollama."""
        return LLMConfig(
            provider="ollama",
            model="llama3",
            temperature=0.3,
            max_tokens=100,
            ollama_base_url="http://localhost:11434"
        )

    @pytest.fixture
    def mock_http_client(self) -> Mock:
        """Create mock HTTP client."""
        return Mock(spec=HttpClient)

    @pytest.fixture
    def adapter(self) -> OllamaAdapter:
        """Create Ollama adapter instance."""
        return OllamaAdapter()

    def test_chat_success(
        self, 
        adapter: OllamaAdapter, 
        config: LLMConfig, 
        mock_http_client: Mock
    ) -> None:
        """Test successful Ollama chat request."""
        mock_response = {
            "message": {"content": "Hello from Llama!"},
            "model": "llama3",
            "eval_count": 42,
            "done": True
        }
        mock_http_client.post.return_value = mock_response

        messages: List[ChatMessage] = [
            {"role": "user", "content": "Hello"}
        ]

        result = adapter.chat(config, messages, mock_http_client)

        assert result.text == "Hello from Llama!"
        assert result.provider == "ollama"
        assert result.model == "llama3"
        assert result.usage == {"eval_count": 42}

        # Verify request format
        call_kwargs = mock_http_client.post.call_args.kwargs
        payload = call_kwargs["json"]
        
        assert payload["model"] == "llama3"
        assert payload["messages"] == messages
        assert payload["stream"] is False
        assert payload["options"]["temperature"] == 0.3
        assert payload["options"]["num_predict"] == 100

    def test_chat_no_max_tokens(
        self, 
        adapter: OllamaAdapter, 
        mock_http_client: Mock
    ) -> None:
        """Test Ollama chat without max_tokens."""
        config = LLMConfig(
            provider="ollama",
            model="llama3",
            max_tokens=None
        )

        mock_response = {
            "message": {"content": "Response"}
        }
        mock_http_client.post.return_value = mock_response

        adapter.chat(config, [{"role": "user", "content": "test"}], mock_http_client)

        call_kwargs = mock_http_client.post.call_args.kwargs
        payload = call_kwargs["json"]
        
        assert "num_predict" not in payload["options"]

    def test_chat_empty_message_content(
        self, 
        adapter: OllamaAdapter, 
        config: LLMConfig, 
        mock_http_client: Mock
    ) -> None:
        """Test Ollama chat with empty message content."""
        mock_response = {
            "message": {"content": ""}
        }
        mock_http_client.post.return_value = mock_response

        result = adapter.chat(config, [{"role": "user", "content": "test"}], mock_http_client)

        assert result.text == ""

    def test_chat_no_message_content(
        self, 
        adapter: OllamaAdapter, 
        config: LLMConfig, 
        mock_http_client: Mock
    ) -> None:
        """Test Ollama chat with missing content field."""
        mock_response = {
            "message": {}  # No content field
        }
        mock_http_client.post.return_value = mock_response

        result = adapter.chat(config, [{"role": "user", "content": "test"}], mock_http_client)

        assert result.text == ""

    def test_chat_malformed_response_no_message(
        self, 
        adapter: OllamaAdapter, 
        config: LLMConfig, 
        mock_http_client: Mock
    ) -> None:
        """Test Ollama chat with response missing message field."""
        mock_response = {"model": "llama3"}  # No message field
        mock_http_client.post.return_value = mock_response

        result = adapter.chat(config, [{"role": "user", "content": "test"}], mock_http_client)

        assert result.text == ""

    def test_chat_invalid_message_type(
        self, 
        adapter: OllamaAdapter, 
        config: LLMConfig, 
        mock_http_client: Mock
    ) -> None:
        """Test Ollama chat with message field as wrong type."""
        mock_response = {"message": "not an object"}
        mock_http_client.post.return_value = mock_response

        with pytest.raises(LLMError, match="Ollama: unexpected response format"):
            adapter.chat(config, [{"role": "user", "content": "test"}], mock_http_client)

    def test_no_authentication_required(
        self, 
        adapter: OllamaAdapter, 
        mock_http_client: Mock
    ) -> None:
        """Test that Ollama doesn't require authentication."""
        config = LLMConfig(
            provider="ollama",
            model="llama3"
            # No API keys needed
        )

        mock_response = {
            "message": {"content": "Response"}
        }
        mock_http_client.post.return_value = mock_response

        # Should not raise authentication error
        result = adapter.chat(config, [{"role": "user", "content": "test"}], mock_http_client)
        assert result.text == "Response"