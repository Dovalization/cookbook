"""
shared/llm.py — Provider-agnostic LLM client for Cookbook.

Goals
- Single interface for chat-like completions across providers.
- Local-first: Ollama works out of the box if running locally.
- Minimal deps: only `requests` and stdlib.
- Resilient: timeouts + simple retry with exponential backoff.
- Testable: pure formatting/adapter logic isolated and covered by pytest.

Usage
-------
from shared.llm import LLM, LLMConfig

llm = LLM.from_env()  # or LLM(LLMConfig(provider="ollama", model="llama3"))
result = llm.chat([
    {"role": "system", "content": "Be concise."},
    {"role": "user", "content": "Summarize Cookbook in one line."},
])
print(result.text)        # normalized primary text
print(result.provider)    # "openai" | "anthropic" | "ollama"
print(result.raw)         # raw provider JSON (for debugging)

Environment variables (if using from_env)
-----------------------------------------
LLM_PROVIDER= openai | anthropic | ollama
LLM_MODEL= (e.g., gpt-4o-mini | claude-3-5-sonnet-20240620 | llama3)
OPENAI_API_KEY=...
OPENAI_BASE_URL= (optional, default https://api.openai.com)
ANTHROPIC_API_KEY=...
ANTHROPIC_API_URL= (optional, default https://api.anthropic.com)
ANTHROPIC_VERSION= (optional, default 2023-06-01)
OLLAMA_BASE_URL= (optional, default http://localhost:11434)
LLM_TIMEOUT_S= (optional, default 60)
LLM_MAX_RETRIES= (optional, default 3)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Callable, List, Literal, Optional, TypedDict

from shared.http_client import HttpClient
from shared.adapters import OpenAIAdapter, AnthropicAdapter, OllamaAdapter
from shared.errors import LLMError

# Supported providers are captured as a Literal for type-safety and autocompletion.
Provider = Literal["openai", "anthropic", "ollama"]


# Standardized message format we accept from callers.
class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


# ---------------
# Configuration
# ---------------

@dataclass(frozen=True)
class LLMConfig:
    """
    Immutable configuration for the LLM client.

    Notes:
    - `provider` and `model` are required.
    - Provider-specific keys (e.g., OPENAI_API_KEY) are optional but required
      at runtime if that provider is selected.
    - Defaults bias toward local-first (Ollama).
    """
    provider: Provider
    model: str
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com"
    # Anthropic
    anthropic_api_key: Optional[str] = None
    anthropic_api_url: str = "https://api.anthropic.com"
    anthropic_version: str = "2023-06-01"
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    # Common
    timeout_s: int = 60
    max_retries: int = 3
    # Behavior
    temperature: float = 0.2
    max_tokens: Optional[int] = None  # provider-specific default if None

    @staticmethod
    def from_env() -> "LLMConfig":
        """
        Build an LLMConfig from environment variables.

        Defaults:
        - Provider: "ollama"
        - Model: "llama3"
        - Reasonable timeouts/retries for CLI usage
        """
        provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        model = os.getenv("LLM_MODEL", "llama3")
        return LLMConfig(
            provider=provider,  # type: ignore[arg-type]
            model=model,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            anthropic_api_url=os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com"),
            anthropic_version=os.getenv("ANTHROPIC_VERSION", "2023-06-01"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            timeout_s=int(os.getenv("LLM_TIMEOUT_S", "60")),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS")) if os.getenv("LLM_MAX_TOKENS") else None,
        )

    # Convenience URL builders so provider methods remain tiny.
    def openai_url(self) -> str:
        return f"{self.openai_base_url.rstrip('/')}/v1/chat/completions"

    def anthropic_url(self) -> str:
        return f"{self.anthropic_api_url.rstrip('/')}/v1/messages"

    def ollama_url(self) -> str:
        return f"{self.ollama_base_url.rstrip('/')}/api/chat"


# ---------------
# Unified result
# ---------------

@dataclass
class LLMResult:
    """
    Normalized response returned by .chat():
    - text: the main assistant message content
    - raw: provider's full JSON (handy for debugging/metrics)
    - provider/model: echo back what was used
    - usage: token usage or eval count (provider-specific)
    """
    text: str
    raw: Dict[str, Any]
    provider: Provider
    model: str
    usage: Optional[Dict[str, Any]] = None

    @classmethod
    def from_provider(cls, provider: Provider, raw: Dict[str, Any], text: str, model: str, usage: Optional[Any] = None) -> "LLMResult":
        return cls(text=text, raw=raw, provider=provider, model=model, usage=usage)


# ---------------
# Main client
# ---------------

class LLM:
    """
    Thin façade over multiple LLM providers exposing a single `chat()` method.

    The provider-specific methods (_chat_openai/_chat_anthropic/_chat_ollama)
    handle payload translation and response normalization. Network calls go
    through a single retry helper for consistent resilience behavior.
    """

    def __init__(self, config: LLMConfig):
        self.cfg = config
        # HttpClient encapsulates session + retry behaviour.
        self._client = HttpClient(timeout_s=self.cfg.timeout_s, max_retries=self.cfg.max_retries)
        # Adapter instances handle provider-specific payload/parse logic.
        self._adapters: Dict[str, Callable[[], Any]] = {
            "openai": OpenAIAdapter(),
            "anthropic": AnthropicAdapter(),
            "ollama": OllamaAdapter(),
        }

    @staticmethod
    def from_env() -> "LLM":
        """Convenience constructor using LLMConfig.from_env()."""
        return LLM(LLMConfig.from_env())

    # -------------------------
    # Public interface
    # -------------------------
    def chat(self, messages: List[ChatMessage]) -> LLMResult:
        """
        Perform a chat-like completion with a normalized message format.

        Parameters:
          messages: list of {"role": "...", "content": "..."} dicts.

        Returns:
          LLMResult with unified fields and the raw provider JSON.

        Routing:
          Dispatches to the provider-specific method based on config.
        """

        handler = self._providers.get(self.cfg.provider)
        if not handler:
            raise LLMError(f"Unsupported provider: {self.cfg.provider}")
        return handler(messages)

    # -------------------------
    # Provider routing
    # -------------------------
    def _chat_openai(self, messages: List[ChatMessage]) -> LLMResult:
        """Dispatch to the OpenAI adapter."""
        return self._adapters["openai"].chat(self.cfg, messages, self._client)

    def _chat_anthropic(self, messages: List[ChatMessage]) -> LLMResult:
        """Dispatch to the Anthropic adapter."""
        return self._adapters["anthropic"].chat(self.cfg, messages, self._client)

    def _chat_ollama(self, messages: List[ChatMessage]) -> LLMResult:
        """Dispatch to the Ollama adapter."""
        return self._adapters["ollama"].chat(self.cfg, messages, self._client)



# Helper functions moved to adapters; LLM is now a thin dispatcher.
