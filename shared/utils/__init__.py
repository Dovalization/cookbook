"""
Common utilities for Cookbook scripts.
"""

from .logging import setup_logging, get_logger
from .cli import (
    create_base_parser,
    add_file_input,
    add_ai_options,
    add_file_options,
    validate_file_exists,
    print_success,
    print_error
)
from .files import (
    save_output,
    move_to_processed,
    add_timestamp_to_filename
)

__all__ = [
    # Logging
    "setup_logging",
    "get_logger",
    
    # CLI utilities
    "create_base_parser",
    "add_file_input", 
    "add_ai_options",
    "add_file_options",
    "validate_file_exists",
    "print_success",
    "print_error",
    
    # File utilities
    "save_output",
    "move_to_processed", 
    "add_timestamp_to_filename",
]
