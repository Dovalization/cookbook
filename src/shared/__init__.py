"""
Shared components for Cookbook automation scripts.

This package provides all the core functionality needed to build
automation scripts with consistent patterns and interfaces.
"""

# Core types and constants
from .core import (
    ChatMessage,
    Provider,
    ProviderName, 
    ProcessingResult,
    DEFAULT_PROVIDER,
    DEFAULT_MODEL,
)

# LLM abstraction
from .llm import LLM, LLMConfig, LLMResult

# Document processing pipeline
from .document_processor import (
    RawDocument,
    ProcessedDocument, 
    DocumentProcessor,
    create_raw_document_from_file,
)

# Utilities
from .utils import (
    setup_logging,
    get_logger,
    create_base_parser,
    save_output,
    move_to_processed,
)

# Configuration
from .config import config

__all__ = [
    # Core types
    "ChatMessage",
    "Provider", 
    "ProviderName",
    "ProcessingResult",
    "DEFAULT_PROVIDER",
    "DEFAULT_MODEL",
    
    # LLM
    "LLM",
    "LLMConfig",
    "LLMResult",
    
    # Document processing
    "RawDocument",
    "ProcessedDocument",
    "DocumentProcessor", 
    "create_raw_document_from_file",
    
    # Utilities
    "setup_logging",
    "get_logger",
    "create_base_parser",
    "save_output",
    "move_to_processed",
    
    # Configuration
    "config",
]
