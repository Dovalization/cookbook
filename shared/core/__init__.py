"""
Core types and constants for Cookbook.

This module provides centralized type definitions and constants
to avoid duplication and circular imports throughout the project.
"""

from .types import (
    ChatMessage,
    Provider, 
    ProviderName,
    ProcessingResult
)

from .constants import (
    # LLM defaults
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
    
    # File processing
    DEFAULT_INBOX,
    DEFAULT_OUTPUT,
    DEFAULT_BACKUP,
    MAX_FILE_SIZE_MB,
    MAX_CONTENT_LENGTH_FOR_AI,
    MAX_CONTENT_LENGTH_FOR_TAGS,
    
    # Logging
    DEFAULT_LOG_LEVEL,
    DEFAULT_LOG_FORMAT,
)

__all__ = [
    # Types
    "ChatMessage",
    "Provider", 
    "ProviderName",
    "ProcessingResult",
    
    # Constants
    "DEFAULT_PROVIDER",
    "DEFAULT_MODEL", 
    "DEFAULT_TEMPERATURE",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_TIMEOUT_S",
    "DEFAULT_MAX_RETRIES",
    "OPENAI_BASE_URL",
    "ANTHROPIC_BASE_URL", 
    "ANTHROPIC_VERSION",
    "OLLAMA_BASE_URL",
    "DEFAULT_INBOX",
    "DEFAULT_OUTPUT",
    "DEFAULT_BACKUP",
    "MAX_FILE_SIZE_MB",
    "MAX_CONTENT_LENGTH_FOR_AI", 
    "MAX_CONTENT_LENGTH_FOR_TAGS",
    "DEFAULT_LOG_LEVEL",
    "DEFAULT_LOG_FORMAT",
]
