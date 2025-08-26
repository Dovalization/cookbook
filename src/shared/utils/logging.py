"""
Centralized logging setup for all Cookbook scripts.
"""

import logging
import sys
from pathlib import Path
from shared.core import DEFAULT_LOG_LEVEL, DEFAULT_LOG_FORMAT


def setup_logging(
    name: str,
    level: str | None = None,
    log_file: Path | str | None = None,
    format_string: str | None = None
) -> logging.Logger:
    """
    Set up logging for a script with sensible defaults.
    
    Args:
        name: Logger name (usually __name__)
        level: Log level (defaults to env var or INFO)
        log_file: Optional file to write logs to
        format_string: Custom format string
    
    Returns:
        Configured logger instance
    """
    import os
    
    # Use provided level, env var, or default
    log_level = level or os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)
    format_str = format_string or DEFAULT_LOG_FORMAT
    
    # Configure root logger if not already done
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=format_str,
            handlers=[logging.StreamHandler(sys.stdout)]
        )
    
    # Add file handler if requested
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(format_str))
        root.addHandler(file_handler)
    
    # Return logger for the specific module
    logger = logging.getLogger(name)
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with standard Cookbook formatting.
    
    This is a lightweight alternative to setup_logging for modules
    that don't need custom configuration.
    """
    return logging.getLogger(name)
