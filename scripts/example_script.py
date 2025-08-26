#!/usr/bin/env python3
"""
Recipe: Example Script
Purpose: Template for new automation scripts
Input: Any text file
Output: Processed text file with word count
Usage: python -m scripts.example_script input.txt
"""

import argparse
import logging
from pathlib import Path
from typing import List, Optional

from shared.config import config
from shared.file_utils import save_output, move_to_processed

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_file(input_path: Path, tags: List[str] = None) -> Path:
    """
    Process a file and return the output path.
    
    Args:
        input_path: Path to input file
        tags: Optional tags (not used in this simple version)
    
    Returns:
        Path to processed file
    """
    logger.info(f"Processing file: {input_path}")
    
    # Read input
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Process content (example: add word count and metadata)
    word_count = len(content.split())
    char_count = len(content)
    line_count = len(content.splitlines())
    
    processed_content = f"""# Processed: {input_path.name}

**File Statistics:**
- Word count: {word_count}
- Character count: {char_count}
- Line count: {line_count}
- Original file: {input_path}
- Processed: {logger.handlers[0].formatter.formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}

---

{content}
"""
    
    # Save output
    output_filename = f"processed_{input_path.name}"
    output_path = save_output(processed_content, output_filename, "processed_files")
    
    logger.info(f"Created processed file: {output_path}")
    return output_path

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Example Cookbook script")
    parser.add_argument("input", type=Path, help="Input file to process")
    parser.add_argument("--tags", nargs="+", help="Tags to apply (placeholder)")
    parser.add_argument("--move-original", action="store_true", 
                       help="Move original file to processed folder")
    
    args = parser.parse_args()
    
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return 1
    
    try:
        output_path = process_file(args.input, args.tags)
        print(f"✓ Processed: {output_path}")
        
        if args.move_original:
            moved_path = move_to_processed(args.input)
            print(f"✓ Moved original to: {moved_path}")
        
        return 0
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return 1

if __name__ == "__main__":
    exit(main())