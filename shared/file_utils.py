"""Basic file utilities for Cookbook scripts."""

import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from .config import config

def save_output(content: str, filename: str, subfolder: str = "") -> Path:
    """
    Save content to a file in the output directory.
    
    Args:
        content: The content to save
        filename: Name for the output file
        subfolder: Optional subfolder within output directory
    
    Returns:
        Path to the saved file
    """
    # Create output directory structure
    output_dir = config.OUTPUT_PATH / subfolder if subfolder else config.OUTPUT_PATH
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Handle duplicate filenames
    output_path = output_dir / filename
    counter = 1
    while output_path.exists():
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        output_path = output_dir / f"{stem}-{counter}{suffix}"
        counter += 1
    
    # Write file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return output_path

def move_to_processed(input_path: Path, subfolder: str = "processed") -> Path:
    """
    Move a processed file to avoid reprocessing.
    
    Args:
        input_path: Path to the input file
        subfolder: Subfolder to move to (default: "processed")
    
    Returns:
        Path to the moved file
    """
    processed_dir = input_path.parent / subfolder
    processed_dir.mkdir(exist_ok=True)
    
    processed_path = processed_dir / input_path.name
    counter = 1
    while processed_path.exists():
        stem = input_path.stem
        suffix = input_path.suffix
        processed_path = processed_dir / f"{stem}-{counter}{suffix}"
        counter += 1
    
    shutil.move(str(input_path), str(processed_path))
    return processed_path

def add_timestamp_to_filename(filename: str) -> str:
    """Add timestamp to filename to avoid collisions."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    return f"{timestamp}_{stem}{suffix}"