"""
Provider adapters for different LLM APIs.

Clean implementation using centralized types and no circular imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol, runtime_checkable

from ..core import ChatMessage, Provider
from ..errors import LLMAuthError, LLMError
from .http_client import HttpClient


# ============================================================================
# Protocols  
# ============================================================================

@runtime_checkable
class LLMConfig(Protocol):
    """Protocol for LLM configuration objects."""
    model: str
    temperature: float
    max_tokens: int | None
    anthropic_version: str
    openai_api_key: str | None
    anthropic_api_key: str | None

    def openai_url(self) -> str: ...
    def anthropic_url(self) -> str: ...
    def ollama_url(self) -> str: ...


@dataclass
class LLMResult:
    """Result from LLM provider."""
    text: str
    raw: Dict[str, Any]
    provider: str
    model: str
    usage: Dict[str, Any] | None = None


# ============================================================================
# Base Adapter
# ============================================================================

class BaseAdapter:
    """Base class with common utilities for all adapters."""
    
    JSON_CT = "application/json"

    @staticmethod
    def require(value: str | None, name: str) -> str:
        """Require a non-empty value or raise auth error."""
        if not value:
            raise LLMAuthError(f"Missing {name}")
        return value

    @staticmethod
    def ensure_dict(obj: Any, provider_name: str) -> Dict[str, Any]:
        """Ensure response is a dictionary."""
        if not isinstance(obj, dict):
            raise LLMError(f"{provider_name}: expected JSON object, got {type(obj)}")
        return obj

    @staticmethod
    def split_system_message(messages: List[ChatMessage]) -> tuple[str | None, List[ChatMessage]]:
        """Extract first system message and return (system_prompt, other_messages)."""
        system: str | None = None
        core: List[ChatMessage] = []
        
        for msg in messages:
            if msg["role"] == "system" and system is None:
                system = msg["content"]
            else:
                core.append(msg)
        
        return system, core


# ============================================================================
# Provider-Specific Adapters
# ============================================================================

class OpenAIAdapter(BaseAdapter):
    """Adapter for OpenAI API."""

    def chat(self, cfg: LLMConfig, messages: List[ChatMessage], client: HttpClient) -> LLMResult:
        api_key = self.require(cfg.openai_api_key, "OPENAI_API_KEY")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": self.JSON_CT,
        }
        
        payload = {
            "model": cfg.model,
            "messages": messages,
            "temperature": cfg.temperature,
        }
        if cfg.max_tokens is not None:
            payload["max_tokens"] = cfg.max_tokens

        raw = self.ensure_dict(
            client.post(cfg.openai_url(), headers=headers, json=payload), 
            "openai"
        )
        
        # Parse response
        try:
            text = raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise LLMError(f"OpenAI: unexpected response format: {e}") from e

        return LLMResult(
            text=text,
            raw=raw,
            provider=Provider.OPENAI.value,
            model=cfg.model,
            usage=raw.get("usage")
        )


class AnthropicAdapter(BaseAdapter):
    """Adapter for Anthropic API."""

    def chat(self, cfg: LLMConfig, messages: List[ChatMessage], client: HttpClient) -> LLMResult:
        api_key = self.require(cfg.anthropic_api_key, "ANTHROPIC_API_KEY")
        system_prompt, core_messages = self.split_system_message(messages)
        
        headers = {
            "x-api-key": api_key,
            "anthropic-version": cfg.anthropic_version,
            "content-type": self.JSON_CT,
        }
        
        # Convert messages to Anthropic format
        anthropic_messages = [
            {
                "role": msg["role"] if msg["role"] in ("user", "assistant") else "user",
                "content": [{"type": "text", "text": msg["content"]}],
            }
            for msg in core_messages
        ]
        
        payload = {
            "model": cfg.model,
            "max_tokens": cfg.max_tokens or 1024,
            "temperature": cfg.temperature,
            "messages": anthropic_messages,
        }
        if system_prompt:
            payload["system"] = system_prompt

        raw = self.ensure_dict(
            client.post(cfg.anthropic_url(), headers=headers, json=payload),
            "anthropic"
        )
        
        # Parse response
        try:
            blocks = raw["content"]
            if not isinstance(blocks, list):
                raise TypeError("content is not a list")
            text = "".join(
                block.get("text", "")
                for block in blocks
                if isinstance(block, dict) and block.get("type") == "text"
            ).strip()
        except (KeyError, TypeError) as e:
            raise LLMError(f"Anthropic: unexpected response format: {e}") from e

        return LLMResult(
            text=text,
            raw=raw,
            provider=Provider.ANTHROPIC.value,
            model=cfg.model,
            usage=raw.get("usage")
        )


class OllamaAdapter(BaseAdapter):
    """Adapter for Ollama API."""

    def chat(self, cfg: LLMConfig, messages: List[ChatMessage], client: HttpClient) -> LLMResult:
        payload = {
            "model": cfg.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": cfg.temperature,
            }
        }
        
        if cfg.max_tokens is not None:
            payload["options"]["num_predict"] = cfg.max_tokens

        raw = self.ensure_dict(
            client.post(cfg.ollama_url(), json=payload),
            "ollama"
        )
        
        # Parse response
        try:
            message = raw.get("message", {})
            if not isinstance(message, dict):
                raise TypeError("message is not an object")
            text = message.get("content", "") or ""
        except Exception as e:
            raise LLMError(f"Ollama: unexpected response format: {e}") from e

        return LLMResult(
            text=text,
            raw=raw,
            provider=Provider.OLLAMA.value,
            model=cfg.model,
            usage={"eval_count": raw.get("eval_count")}
        )
