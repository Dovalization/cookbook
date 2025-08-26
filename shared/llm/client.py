"""
Main LLM client with provider abstraction.

Clean implementation with no circular imports.
"""

from typing import List

from ..core import ChatMessage, MAX_CONTENT_LENGTH_FOR_AI, MAX_CONTENT_LENGTH_FOR_TAGS
from ..errors import LLMError
from .config import LLMConfig
from .adapters import LLMResult, OpenAIAdapter, AnthropicAdapter, OllamaAdapter
from .http_client import HttpClient


class LLM:
    """
    Provider-agnostic LLM client.
    
    Supports OpenAI, Anthropic, and Ollama with a unified interface.
    """

    def __init__(self, config: LLMConfig):
        self.cfg = config
        self._client = HttpClient(
            timeout_s=self.cfg.timeout_s,
            max_retries=self.cfg.max_retries
        )
        
        # Provider adapters
        self._adapters = {
            "openai": OpenAIAdapter(),
            "anthropic": AnthropicAdapter(), 
            "ollama": OllamaAdapter(),
        }

    @classmethod
    def from_env(cls) -> "LLM":
        """Create LLM client from environment variables."""
        return cls(LLMConfig.from_env())

    def chat(self, messages: List[ChatMessage]) -> LLMResult:
        """
        Send chat messages to configured LLM provider.
        
        Args:
            messages: List of chat messages
            
        Returns:
            LLMResult with text response and metadata
            
        Raises:
            LLMError: If provider is unsupported or request fails
        """
        adapter = self._adapters.get(self.cfg.provider)
        if not adapter:
            raise LLMError(f"Unsupported provider: {self.cfg.provider}")
        
        return adapter.chat(self.cfg, messages, self._client)

    # ============================================================================
    # Convenience Methods
    # ============================================================================

    def summarize(self, text: str, style: str = "concise") -> str:
        """
        Summarize text with optional style guidance.
        
        Args:
            text: Text to summarize (will be truncated if too long)
            style: Summary style (e.g., "concise", "bullet-point", "detailed")
            
        Returns:
            Summary text
        """
        # Truncate input to avoid overwhelming the model
        content = text[:MAX_CONTENT_LENGTH_FOR_AI]
        
        messages = [
            {"role": "system", "content": f"Summarize the following text in a {style} manner."},
            {"role": "user", "content": content}
        ]
        
        result = self.chat(messages)
        return result.text

    def extract_tags(self, text: str, max_tags: int = 5) -> List[str]:
        """
        Extract relevant tags from text.
        
        Args:
            text: Text to extract tags from (will be truncated if too long)
            max_tags: Maximum number of tags to extract
            
        Returns:
            List of tag strings
        """
        # Truncate input for tag extraction
        content = text[:MAX_CONTENT_LENGTH_FOR_TAGS]
        
        messages = [
            {
                "role": "system", 
                "content": f"Extract up to {max_tags} relevant tags from the text. Return only the tags, one per line."
            },
            {"role": "user", "content": content}
        ]
        
        result = self.chat(messages)
        
        # Parse tags from response
        tags = [tag.strip() for tag in result.text.split('\n') if tag.strip()]
        return tags[:max_tags]  # Ensure we don't exceed max_tags

    def analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment analysis result
        """
        content = text[:MAX_CONTENT_LENGTH_FOR_AI]
        
        messages = [
            {
                "role": "system",
                "content": "Analyze the sentiment of the following text. Respond with just: positive, negative, or neutral."
            },
            {"role": "user", "content": content}
        ]
        
        result = self.chat(messages)
        return result.text.strip().lower()
