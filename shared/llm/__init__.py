"""
LLM abstraction layer for Cookbook.

Provides a clean, provider-agnostic interface for working with
OpenAI, Anthropic, and Ollama APIs.
"""

from .client import LLM
from .config import LLMConfig
from .adapters import LLMResult

__all__ = [
    "LLM",
    "LLMConfig", 
    "LLMResult",
]
