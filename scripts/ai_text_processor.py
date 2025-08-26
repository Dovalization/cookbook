#!/usr/bin/env python3
"""
Recipe: AI-Enhanced Text Processor
Purpose: Process text files with AI insights (summary + tags)
Input: Any text file
Output: Processed text file with AI analysis
Usage: python -m scripts.ai_text_processor input.txt
"""

import argparse
import logging
from pathlib import Path
from typing import List, Optional

from shared.config import config
from shared.file_utils import save_output, move_to_processed
from shared.llm import LLM

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_file(input_path: Path, enable_ai: bool = True, tags: List[str] = None) -> Path:
    """
    Process a file with AI insights and return the output path.
    
    Args:
        input_path: Path to input file
        enable_ai: Whether to use AI for processing (fallback to basic stats)
        tags: Optional manual tags
    
    Returns:
        Path to processed file
    """
    logger.info(f"Processing file: {input_path}")
    
    # Read input
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Basic statistics
    word_count = len(content.split())
    char_count = len(content)
    line_count = len(content.splitlines())
    
    # AI processing if enabled
    summary = ""
    ai_tags = []
    
    if enable_ai:
        try:
            logger.info("Using AI to analyze content...")
            llm = LLM.from_env()
            
            # Get AI summary (only for longer texts to avoid overhead)
            if word_count > 50:
                summary = llm.summarize(content[:2000], style="bullet-point")  # Limit input size
                logger.info(f"AI summary generated: {len(summary)} chars")
            
            # Get AI tags
            ai_tags = llm.extract_tags(content[:1000], max_tags=7)
            logger.info(f"AI tags extracted: {ai_tags}")
            
        except Exception as e:
            logger.warning(f"AI processing failed, falling back to basic processing: {e}")
            enable_ai = False
    
    # Combine manual and AI tags
    all_tags = list(set((tags or []) + ai_tags))
    
    # Build processed content
    processed_content = f"""# Processed: {input_path.name}

## File Statistics
- **Word count:** {word_count:,}
- **Character count:** {char_count:,}
- **Line count:** {line_count:,}
- **Original file:** {input_path}
- **AI processing:** {'✓ Enabled' if enable_ai else '✗ Disabled'}

## Tags
{', '.join(f'`{tag}`' for tag in all_tags) if all_tags else '_No tags_'}

"""
    
    # Add AI summary if available
    if summary:
        processed_content += f"""## AI Summary
{summary}

"""
    
    # Add original content
    processed_content += f"""---

## Original Content

{content}
"""
    
    # Save output
    output_filename = f"processed_{input_path.stem}.md"
    output_path = save_output(processed_content, output_filename, "processed_files")
    
    logger.info(f"Created processed file: {output_path}")
    return output_path

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="AI-enhanced text processing")
    parser.add_argument("input", type=Path, help="Input file to process")
    parser.add_argument("--tags", nargs="+", help="Manual tags to add")
    parser.add_argument("--no-ai", action="store_true", 
                       help="Disable AI processing (basic stats only)")
    parser.add_argument("--move-original", action="store_true", 
                       help="Move original file to processed folder")
    
    args = parser.parse_args()
    
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return 1
    
    try:
        output_path = process_file(
            args.input, 
            enable_ai=not args.no_ai,
            tags=args.tags
        )
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
