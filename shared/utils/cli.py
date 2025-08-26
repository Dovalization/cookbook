"""
Common CLI utilities for Cookbook scripts.
"""

import argparse
from pathlib import Path
from typing import Optional


def create_base_parser(description: str, add_common_args: bool = True) -> argparse.ArgumentParser:
    """
    Create a base argument parser with common Cookbook arguments.
    
    Args:
        description: Description for the script
        add_common_args: Whether to add common arguments (--verbose, --quiet, etc.)
    
    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(description=description)
    
    if add_common_args:
        parser.add_argument(
            "--verbose", "-v", 
            action="store_true",
            help="Enable verbose output"
        )
        parser.add_argument(
            "--quiet", "-q",
            action="store_true", 
            help="Suppress non-error output"
        )
    
    return parser


def add_file_input(parser: argparse.ArgumentParser, required: bool = True) -> None:
    """Add standard file input argument to parser."""
    parser.add_argument(
        "input",
        type=Path,
        help="Input file to process" + ("" if required else " (optional)"),
        nargs=None if required else "?"
    )


def add_ai_options(parser: argparse.ArgumentParser) -> None:
    """Add common AI processing options to parser."""
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Disable AI processing (basic stats only)"
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        help="Manual tags to add"
    )


def add_file_options(parser: argparse.ArgumentParser) -> None:
    """Add common file processing options to parser.""" 
    parser.add_argument(
        "--move-original",
        action="store_true",
        help="Move original file to processed folder"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Custom output directory"
    )


def validate_file_exists(file_path: Path, logger) -> bool:
    """
    Validate that a file exists and log error if not.
    
    Returns:
        True if file exists, False otherwise
    """
    if not file_path.exists():
        logger.error(f"Input file not found: {file_path}")
        return False
    return True


def print_success(message: str) -> None:
    """Print a success message with checkmark."""
    print(f"✓ {message}")


def print_error(message: str) -> None:
    """Print an error message with X mark."""
    print(f"✗ {message}")
