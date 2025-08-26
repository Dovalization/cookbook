#!/usr/bin/env python3
"""
Recipe: AI-Enhanced Text Processor
Purpose: Process text files with AI insights (summary + tags)
Input: Any text file
Output: Processed markdown file with AI analysis
Usage: python -m scripts.ai_text_processor input.txt
"""

from pathlib import Path
from typing import List, Optional
import time

from shared.core import ProcessingResult
from shared.llm import LLM
from shared.utils import (
    setup_logging,
    create_base_parser,
    add_file_input,
    add_ai_options,
    add_file_options,
    validate_file_exists,
    print_success,
    print_error,
    save_output,
    move_to_processed
)

logger = setup_logging(__name__)


def process_file(input_path: Path, enable_ai: bool = True, tags: Optional[List[str]] = None) -> ProcessingResult:
    """
    Process a file with AI insights and return structured results.
    
    Args:
        input_path: Path to input file
        enable_ai: Whether to use AI for processing
        tags: Optional manual tags to add
    
    Returns:
        ProcessingResult with success status and metadata
    """
    start_time = time.time()
    logger.info(f"Processing file: {input_path}")
    
    try:
        # Read input file
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Calculate basic statistics
        stats = {
            "word_count": len(content.split()),
            "char_count": len(content),
            "line_count": len(content.splitlines()),
        }
        
        # AI processing if enabled
        summary = ""
        ai_tags = []
        
        if enable_ai:
            try:
                logger.info("Analyzing content with AI...")
                llm = LLM.from_env()
                
                # Get summary for longer texts
                if stats["word_count"] > 50:
                    summary = llm.summarize(content, style="bullet-point")
                    logger.info(f"Generated summary: {len(summary)} chars")
                
                # Extract tags
                ai_tags = llm.extract_tags(content, max_tags=7)
                logger.info(f"Extracted tags: {ai_tags}")
                
            except Exception as e:
                logger.warning(f"AI processing failed, using basic processing: {e}")
                enable_ai = False
        
        # Combine tags
        all_tags = list(set((tags or []) + ai_tags))
        
        # Build processed content
        processed_content = _build_markdown_output(
            input_path, stats, all_tags, summary, content, enable_ai
        )
        
        # Save output
        output_filename = f"processed_{input_path.stem}.md"
        output_path = save_output(processed_content, output_filename, "processed_files")
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"Processing completed in {processing_time}ms")
        
        return ProcessingResult(
            success=True,
            input_path=str(input_path),
            output_path=str(output_path),
            error_message=None,
            processing_time_ms=processing_time,
            metadata={
                "word_count": str(stats["word_count"]),
                "ai_enabled": str(enable_ai),
                "tags_count": str(len(all_tags)),
                "has_summary": str(bool(summary)),
            }
        )
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"Processing failed: {e}")
        
        return ProcessingResult(
            success=False,
            input_path=str(input_path),
            output_path=None,
            error_message=str(e),
            processing_time_ms=processing_time,
            metadata={}
        )


def _build_markdown_output(
    input_path: Path,
    stats: dict,
    tags: List[str],
    summary: str,
    content: str,
    ai_enabled: bool
) -> str:
    """Build the markdown output content."""
    
    output = f"""# Processed: {input_path.name}

## File Statistics
- **Word count:** {stats['word_count']:,}
- **Character count:** {stats['char_count']:,}
- **Line count:** {stats['line_count']:,}
- **Original file:** {input_path}
- **AI processing:** {'✓ Enabled' if ai_enabled else '✗ Disabled'}

## Tags
{', '.join(f'`{tag}`' for tag in tags) if tags else '_No tags_'}

"""
    
    # Add AI summary if available
    if summary:
        output += f"""## AI Summary
{summary}

"""
    
    # Add original content
    output += f"""---

## Original Content

{content}
"""
    
    return output


def main():
    """Main CLI interface."""
    parser = create_base_parser("Process text files with AI insights")
    add_file_input(parser)
    add_ai_options(parser)
    add_file_options(parser)
    
    args = parser.parse_args()
    
    # Validate input
    if not validate_file_exists(args.input, logger):
        return 1
    
    # Process file
    result = process_file(
        args.input,
        enable_ai=not args.no_ai,
        tags=args.tags
    )
    
    # Handle results
    if result["success"]:
        print_success(f"Processed: {result['output_path']}")
        print(f"   Processing time: {result['processing_time_ms']}ms")
        print(f"   AI enabled: {result['metadata'].get('ai_enabled', 'unknown')}")
        
        if args.move_original:
            try:
                moved_path = move_to_processed(args.input)
                print_success(f"Moved original to: {moved_path}")
            except Exception as e:
                print_error(f"Failed to move original: {e}")
        
        return 0
    else:
        print_error(f"Processing failed: {result['error_message']}")
        return 1


if __name__ == "__main__":
    exit(main())
