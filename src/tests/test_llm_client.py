"""
Unit tests for LLM client with mocked HTTP dependencies.

Tests the main LLM client functionality without making actual API calls.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List

from shared.llm.client import LLM
from shared.llm.config import LLMConfig
from shared.llm.adapters import LLMResult
from shared.core.types import ChatMessage
from shared.errors import LLMError, LLMAuthError


class TestLLMClient:
    """Test suite for LLM client functionality."""

    @pytest.fixture
    def mock_config(self) -> LLMConfig:
        """Create a test configuration."""
        return LLMConfig(
            provider="ollama",
            model="llama3",
            temperature=0.2,
            max_tokens=100,
            timeout_s=30,
            max_retries=2,
            openai_api_key="test-openai-key",
            anthropic_api_key="test-anthropic-key",
            ollama_base_url="http://localhost:11434"
        )

    @pytest.fixture
    def mock_http_client(self) -> Mock:
        """Create a mock HTTP client."""
        mock_client = Mock()
        mock_client.post.return_value = {
            "message": {"content": "Test response"},
            "model": "llama3",
            "eval_count": 50
        }
        return mock_client

    @pytest.fixture
    def mock_llm_result(self) -> LLMResult:
        """Create a mock LLM result."""
        return LLMResult(
            text="Test response",
            raw={"message": {"content": "Test response"}},
            provider="ollama",
            model="llama3",
            usage={"eval_count": 50}
        )

    @pytest.fixture
    def llm_client(self, mock_config: LLMConfig) -> LLM:
        """Create LLM client with mocked dependencies."""
        with patch('shared.llm.client.HttpClient') as mock_http_class:
            mock_http_class.return_value = Mock()
            return LLM(mock_config)

    def test_llm_initialization(self, mock_config: LLMConfig) -> None:
        """Test LLM client initialization."""
        with patch('shared.llm.client.HttpClient') as mock_http_class:
            llm = LLM(mock_config)
            
            # Check configuration is stored
            assert llm.cfg == mock_config
            
            # Check HTTP client was created with correct parameters
            mock_http_class.assert_called_once_with(
                timeout_s=mock_config.timeout_s,
                max_retries=mock_config.max_retries
            )
            
            # Check adapters are available
            assert "openai" in llm._adapters
            assert "anthropic" in llm._adapters
            assert "ollama" in llm._adapters

    @patch.dict('os.environ', {
        'LLM_PROVIDER': 'openai',
        'LLM_MODEL': 'gpt-4',
        'OPENAI_API_KEY': 'test-key'
    })
    def test_from_env_constructor(self) -> None:
        """Test creating LLM from environment variables."""
        with patch('shared.llm.client.HttpClient'):
            llm = LLM.from_env()
            assert llm.cfg.provider == "openai"
            assert llm.cfg.model == "gpt-4"
            assert llm.cfg.openai_api_key == "test-key"

    def test_chat_success(self, llm_client: LLM, mock_llm_result: LLMResult) -> None:
        """Test successful chat interaction."""
        # Mock the adapter's chat method
        llm_client._adapters["ollama"].chat = Mock(return_value=mock_llm_result)
        
        messages: List[ChatMessage] = [
            {"role": "user", "content": "Hello, world!"}
        ]
        
        result = llm_client.chat(messages)
        
        assert result == mock_llm_result
        llm_client._adapters["ollama"].chat.assert_called_once_with(
            llm_client.cfg, messages, llm_client._client
        )

    def test_chat_unsupported_provider(self, llm_client: LLM) -> None:
        """Test chat with unsupported provider."""
        llm_client.cfg = LLMConfig(provider="unsupported", model="test")  # type: ignore
        
        with pytest.raises(LLMError, match="Unsupported provider: unsupported"):
            llm_client.chat([{"role": "user", "content": "test"}])

    def test_chat_adapter_error(self, llm_client: LLM) -> None:
        """Test chat when adapter raises an error."""
        llm_client._adapters["ollama"].chat = Mock(
            side_effect=LLMAuthError("Authentication failed")
        )
        
        with pytest.raises(LLMAuthError, match="Authentication failed"):
            llm_client.chat([{"role": "user", "content": "test"}])

    def test_summarize_basic(self, llm_client: LLM) -> None:
        """Test basic text summarization."""
        mock_result = LLMResult(
            text="This is a summary",
            raw={},
            provider="ollama", 
            model="llama3"
        )
        llm_client._adapters["ollama"].chat = Mock(return_value=mock_result)
        
        result = llm_client.summarize("This is a long text to summarize.")
        
        assert result == "This is a summary"
        
        # Verify the chat was called with correct system message
        call_args = llm_client._adapters["ollama"].chat.call_args
        messages = call_args[0][1]  # Second argument (messages)
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "concise" in messages[0]["content"]
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "This is a long text to summarize."

    def test_summarize_with_style(self, llm_client: LLM) -> None:
        """Test summarization with custom style."""
        mock_result = LLMResult(text="Bullet summary", raw={}, provider="ollama", model="llama3")
        llm_client._adapters["ollama"].chat = Mock(return_value=mock_result)
        
        llm_client.summarize("Text to summarize", style="bullet-point")
        
        call_args = llm_client._adapters["ollama"].chat.call_args
        messages = call_args[0][1]
        
        assert "bullet-point" in messages[0]["content"]

    def test_summarize_content_truncation(self, llm_client: LLM) -> None:
        """Test that summarize truncates long content."""
        from shared.core.constants import MAX_CONTENT_LENGTH_FOR_AI
        
        mock_result = LLMResult(text="Summary", raw={}, provider="ollama", model="llama3")
        llm_client._adapters["ollama"].chat = Mock(return_value=mock_result)
        
        long_text = "x" * (MAX_CONTENT_LENGTH_FOR_AI + 100)
        llm_client.summarize(long_text)
        
        call_args = llm_client._adapters["ollama"].chat.call_args
        messages = call_args[0][1]
        user_content = messages[1]["content"]
        
        assert len(user_content) == MAX_CONTENT_LENGTH_FOR_AI

    def test_extract_tags_basic(self, llm_client: LLM) -> None:
        """Test basic tag extraction."""
        mock_result = LLMResult(
            text="python\nautomation\nscripting\nai",
            raw={},
            provider="ollama",
            model="llama3"
        )
        llm_client._adapters["ollama"].chat = Mock(return_value=mock_result)
        
        tags = llm_client.extract_tags("This is a Python script for automation.")
        
        assert tags == ["python", "automation", "scripting", "ai"]
        
        # Verify system message mentions tags
        call_args = llm_client._adapters["ollama"].chat.call_args
        messages = call_args[0][1]
        assert "tags" in messages[0]["content"].lower()

    def test_extract_tags_with_max_limit(self, llm_client: LLM) -> None:
        """Test tag extraction respects max_tags parameter."""
        mock_result = LLMResult(
            text="tag1\ntag2\ntag3\ntag4\ntag5\ntag6",
            raw={},
            provider="ollama",
            model="llama3"
        )
        llm_client._adapters["ollama"].chat = Mock(return_value=mock_result)
        
        tags = llm_client.extract_tags("Some text", max_tags=3)
        
        assert len(tags) == 3
        assert tags == ["tag1", "tag2", "tag3"]

    def test_extract_tags_empty_response(self, llm_client: LLM) -> None:
        """Test tag extraction with empty or whitespace response."""
        mock_result = LLMResult(text="  \n  \n  ", raw={}, provider="ollama", model="llama3")
        llm_client._adapters["ollama"].chat = Mock(return_value=mock_result)
        
        tags = llm_client.extract_tags("Some text")
        
        assert tags == []

    def test_analyze_sentiment_positive(self, llm_client: LLM) -> None:
        """Test sentiment analysis returning positive."""
        mock_result = LLMResult(text="Positive", raw={}, provider="ollama", model="llama3")
        llm_client._adapters["ollama"].chat = Mock(return_value=mock_result)
        
        sentiment = llm_client.analyze_sentiment("I love this product!")
        
        assert sentiment == "positive"

    def test_analyze_sentiment_negative(self, llm_client: LLM) -> None:
        """Test sentiment analysis returning negative."""
        mock_result = LLMResult(text="NEGATIVE", raw={}, provider="ollama", model="llama3")
        llm_client._adapters["ollama"].chat = Mock(return_value=mock_result)
        
        sentiment = llm_client.analyze_sentiment("This is terrible.")
        
        assert sentiment == "negative"

    def test_analyze_sentiment_neutral(self, llm_client: LLM) -> None:
        """Test sentiment analysis returning neutral."""
        mock_result = LLMResult(text="neutral", raw={}, provider="ollama", model="llama3")
        llm_client._adapters["ollama"].chat = Mock(return_value=mock_result)
        
        sentiment = llm_client.analyze_sentiment("The sky is blue.")
        
        assert sentiment == "neutral"

    @pytest.mark.parametrize("provider", ["openai", "anthropic", "ollama"])
    def test_chat_with_different_providers(self, mock_config: LLMConfig, provider: str) -> None:
        """Test chat functionality with different providers."""
        mock_config = LLMConfig(
            provider=provider,  # type: ignore
            model="test-model",
            openai_api_key="test-openai-key",
            anthropic_api_key="test-anthropic-key"
        )
        
        mock_result = LLMResult(
            text=f"Response from {provider}",
            raw={},
            provider=provider,
            model="test-model"
        )
        
        with patch('shared.llm.client.HttpClient'):
            llm = LLM(mock_config)
            llm._adapters[provider].chat = Mock(return_value=mock_result)
            
            result = llm.chat([{"role": "user", "content": "test"}])
            
            assert result.text == f"Response from {provider}"
            assert result.provider == provider

    def test_multiple_system_messages_in_chat(self, llm_client: LLM) -> None:
        """Test chat with multiple system messages (should work with adapters)."""
        mock_result = LLMResult(text="Response", raw={}, provider="ollama", model="llama3")
        llm_client._adapters["ollama"].chat = Mock(return_value=mock_result)
        
        messages: List[ChatMessage] = [
            {"role": "system", "content": "You are helpful."},
            {"role": "system", "content": "You are concise."},
            {"role": "user", "content": "Hello"}
        ]
        
        result = llm_client.chat(messages)
        
        assert result.text == "Response"
        # The adapter should handle multiple system messages appropriately
        llm_client._adapters["ollama"].chat.assert_called_once()

    def test_content_length_limits_applied(self, llm_client: LLM) -> None:
        """Test that content length limits are applied correctly."""
        from shared.core.constants import MAX_CONTENT_LENGTH_FOR_TAGS
        
        mock_result = LLMResult(text="tag1\ntag2", raw={}, provider="ollama", model="llama3")
        llm_client._adapters["ollama"].chat = Mock(return_value=mock_result)
        
        long_text = "x" * (MAX_CONTENT_LENGTH_FOR_TAGS + 100)
        llm_client.extract_tags(long_text)
        
        call_args = llm_client._adapters["ollama"].chat.call_args
        messages = call_args[0][1]
        user_content = messages[1]["content"]
        
        assert len(user_content) == MAX_CONTENT_LENGTH_FOR_TAGS