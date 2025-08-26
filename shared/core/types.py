"""
Core types and constants used throughout Cookbook.

This module centralizes type definitions to avoid duplication and circular imports.
"""

from typing import Literal, TypedDict
from enum import Enum

# ============================================================================
# LLM Types
# ============================================================================

class ChatMessage(TypedDict):
    """Standardized message format for all LLM providers."""
    role: Literal["system", "user", "assistant"]
    content: str


class Provider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


# Type alias for provider strings (used in configs)
ProviderName = Literal["openai", "anthropic", "ollama"]

# ============================================================================
# File Processing Types  
# ============================================================================

class ProcessingResult(TypedDict):
    """Standard result format for file processing operations."""
    success: bool
    input_path: str
    output_path: str | None
    error_message: str | None
    processing_time_ms: int
    metadata: dict[str, str]
