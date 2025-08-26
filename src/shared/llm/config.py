"""
Configuration for LLM providers.
"""

import os
from dataclasses import dataclass
from typing import Optional

from ..core import (
    ProviderName, 
    DEFAULT_PROVIDER,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TIMEOUT_S,
    DEFAULT_MAX_RETRIES,
    OPENAI_BASE_URL,
    ANTHROPIC_BASE_URL,
    ANTHROPIC_VERSION,
    OLLAMA_BASE_URL,
)


@dataclass(frozen=True)
class LLMConfig:
    """
    Immutable configuration for LLM providers.
    
    Centralizes all LLM-related settings with sensible defaults
    that bias toward local-first (Ollama) usage.
    """
    provider: ProviderName
    model: str
    
    # Behavior settings
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: Optional[int] = DEFAULT_MAX_TOKENS
    timeout_s: int = DEFAULT_TIMEOUT_S
    max_retries: int = DEFAULT_MAX_RETRIES
    
    # Provider-specific settings
    openai_api_key: Optional[str] = None
    openai_base_url: str = OPENAI_BASE_URL
    
    anthropic_api_key: Optional[str] = None
    anthropic_api_url: str = ANTHROPIC_BASE_URL
    anthropic_version: str = ANTHROPIC_VERSION
    
    ollama_base_url: str = OLLAMA_BASE_URL

    @staticmethod
    def from_env() -> "LLMConfig":
        """
        Create configuration from environment variables.
        
        Environment Variables:
            LLM_PROVIDER: openai | anthropic | ollama (default: ollama)
            LLM_MODEL: Model name (default: llama3)
            LLM_TEMPERATURE: Temperature (default: 0.2)
            LLM_MAX_TOKENS: Max tokens (optional)
            LLM_TIMEOUT_S: Request timeout (default: 60)
            LLM_MAX_RETRIES: Max retries (default: 3)
            
            OPENAI_API_KEY: OpenAI API key
            OPENAI_BASE_URL: OpenAI base URL (optional)
            
            ANTHROPIC_API_KEY: Anthropic API key  
            ANTHROPIC_API_URL: Anthropic API URL (optional)
            ANTHROPIC_VERSION: Anthropic API version (optional)
            
            OLLAMA_BASE_URL: Ollama base URL (optional)
        """
        provider = os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER).lower()
        
        # Validate provider
        if provider not in ("openai", "anthropic", "ollama"):
            raise ValueError(f"Unsupported provider: {provider}")
        
        return LLMConfig(
            provider=provider,  # type: ignore[arg-type]
            model=os.getenv("LLM_MODEL", DEFAULT_MODEL),
            temperature=float(os.getenv("LLM_TEMPERATURE", str(DEFAULT_TEMPERATURE))),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS")) if os.getenv("LLM_MAX_TOKENS") else None,
            timeout_s=int(os.getenv("LLM_TIMEOUT_S", str(DEFAULT_TIMEOUT_S))),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", str(DEFAULT_MAX_RETRIES))),
            
            # Provider-specific
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_base_url=os.getenv("OPENAI_BASE_URL", OPENAI_BASE_URL),
            
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            anthropic_api_url=os.getenv("ANTHROPIC_API_URL", ANTHROPIC_BASE_URL),
            anthropic_version=os.getenv("ANTHROPIC_VERSION", ANTHROPIC_VERSION),
            
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL),
        )

    # URL builders for adapter convenience
    def openai_url(self) -> str:
        """Get OpenAI chat completions endpoint."""
        return f"{self.openai_base_url.rstrip('/')}/v1/chat/completions"

    def anthropic_url(self) -> str:
        """Get Anthropic messages endpoint."""
        return f"{self.anthropic_api_url.rstrip('/')}/v1/messages"

    def ollama_url(self) -> str:
        """Get Ollama chat endpoint."""
        return f"{self.ollama_base_url.rstrip('/')}/api/chat"
