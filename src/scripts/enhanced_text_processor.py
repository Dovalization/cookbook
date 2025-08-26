#!/usr/bin/env python3
"""
Recipe: Enhanced AI Text Processor (v2)
Purpose: Process text files using the new document processing pipeline
Input: Any text file
Output: Rich markdown with AI insights, entities, and metadata
Usage: python -m scripts.enhanced_text_processor input.txt
"""

from pathlib import Path
from typing import List, Optional

from shared.document_processor import DocumentProcessor, create_raw_document_from_file
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


def process_file_with_pipeline(
    input_path: Path, 
    enable_ai: bool = True, 
    manual_tags: Optional[List[str]] = None,
    summary_style: str = "bullet-point",
    extract_entities: bool = True
) -> dict:
    """
    Process a file using the document processing pipeline.
    
    Args:
        input_path: Path to input file
        enable_ai: Whether to use AI processing
        manual_tags: Manual tags to apply
        summary_style: AI summary style
        extract_entities: Whether to extract entities
    
    Returns:
        Dictionary with processing results and metadata
    """
    logger.info(f"Processing with pipeline: {input_path}")
    
    try:
        # Create raw document from file
        raw_doc = create_raw_document_from_file(input_path)
        logger.info(f"Raw document created: {raw_doc.title}")
        
        # Initialize processor
        processor = DocumentProcessor(enable_ai=enable_ai)
        
        # Process document
        processed_doc = processor.process(
            raw_doc,
            manual_tags=manual_tags,
            extract_entities=extract_entities,
            summary_style=summary_style
        )
        
        if not processed_doc.success:
            return {
                "success": False,
                "error": processed_doc.error_message,
                "processing_time_ms": processed_doc.processing_time_ms
            }
        
        # Generate enhanced markdown output
        markdown_content = _generate_enhanced_markdown(processed_doc, raw_doc)
        
        # Save output
        output_filename = f"enhanced_{input_path.stem}.md"
        output_path = save_output(markdown_content, output_filename, "enhanced_processed")
        
        # Update processed document with output path
        processed_doc.output_path = str(output_path)
        
        return {
            "success": True,
            "processed_doc": processed_doc,
            "output_path": str(output_path)
        }
        
    except Exception as e:
        logger.error(f"Pipeline processing failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "processing_time_ms": 0
        }


def _generate_enhanced_markdown(processed_doc, raw_doc) -> str:
    """Generate rich markdown output from processed document."""
    
    # Header with title and metadata
    output = f"""# {raw_doc.title}

> **Processed**: {processed_doc.processed_at.strftime('%Y-%m-%d %H:%M:%S')}  
> **Source**: `{processed_doc.input_path}`  
> **Processing Time**: {processed_doc.processing_time_ms}ms  
> **Content Hash**: `{processed_doc.content_hash}`

"""
    
    # Content Statistics
    stats = processed_doc.content_stats
    output += f"""## 📊 Content Statistics

| Metric | Value |
|--------|-------|
| **Words** | {stats.get('word_count', 0):,} |
| **Characters** | {stats.get('char_count', 0):,} |
| **Lines** | {stats.get('line_count', 0)} |
| **Paragraphs** | {stats.get('paragraph_count', 0)} |
| **Reading Time** | ~{stats.get('reading_time_minutes', 0)} min |
| **Complexity** | {stats.get('complexity', 'unknown').title()} |
| **Avg Word Length** | {stats.get('avg_word_length', 0)} chars |

"""
    
    # Tags Section
    if processed_doc.all_tags:
        tags_display = ' '.join(f'`{tag}`' for tag in processed_doc.all_tags)
        output += f"""## 🏷️ Tags

{tags_display}

"""
    
    # AI Summary
    if processed_doc.ai_summary:
        output += f"""## 🤖 AI Summary

{processed_doc.ai_summary}

"""
    
    # Key Points
    if processed_doc.ai_key_points:
        output += f"""## 🎯 Key Points

"""
        for point in processed_doc.ai_key_points:
            output += f"- {point}\n"
        output += "\n"
    
    # Sentiment Analysis
    if processed_doc.ai_sentiment:
        sentiment_emoji = {
            "positive": "😊",
            "negative": "😞", 
            "neutral": "😐"
        }.get(processed_doc.ai_sentiment, "❓")
        
        output += f"""## 💭 Sentiment Analysis

{sentiment_emoji} **{processed_doc.ai_sentiment.title()}**

"""
    
    # Extracted Entities
    entities = processed_doc.extracted_entities
    if any(entities.values()):
        output += f"""## 🔍 Extracted Entities

"""
        for entity_type, items in entities.items():
            if items:
                output += f"**{entity_type.replace('_', ' ').title()}**: {', '.join(items)}\n"
        output += "\n"
    
    # Processing Details (collapsible)
    output += f"""<details>
<summary>🔧 Processing Details</summary>

### AI Configuration
- **AI Enabled**: {'✅ Yes' if processed_doc.ai_summary else '❌ No'}
- **Summary Generated**: {'✅ Yes' if processed_doc.ai_summary else '❌ No'}  
- **Tags Extracted**: {len(processed_doc.ai_tags)} AI tags
- **Key Points**: {len(processed_doc.ai_key_points)} points extracted

### Content Analysis
- **Content Type**: {raw_doc.content_type}
- **Original Created**: {raw_doc.created_at.strftime('%Y-%m-%d %H:%M:%S') if raw_doc.created_at else 'Unknown'}
- **Processing Notes**: {raw_doc.processing_notes or 'None'}

### Technical Details
- **Content Hash**: `{processed_doc.content_hash}`
- **Processing Time**: {processed_doc.processing_time_ms}ms
- **Timestamp**: {processed_doc.processed_at.isoformat()}

</details>

---

## 📄 Original Content

{raw_doc.content}
"""
    
    return output


def main():
    """Main CLI interface."""
    parser = create_base_parser("Enhanced text processor using document pipeline")
    add_file_input(parser)
    add_ai_options(parser)
    add_file_options(parser)
    
    # Add enhanced processing options
    parser.add_argument(
        "--summary-style",
        choices=["bullet-point", "concise", "detailed", "paragraph"],
        default="bullet-point",
        help="Style for AI summary generation"
    )
    parser.add_argument(
        "--no-entities",
        action="store_true",
        help="Skip entity extraction (dates, emails, etc.)"
    )
    
    args = parser.parse_args()
    
    # Validate input
    if not validate_file_exists(args.input, logger):
        return 1
    
    # Process file
    result = process_file_with_pipeline(
        args.input,
        enable_ai=not args.no_ai,
        manual_tags=args.tags,
        summary_style=args.summary_style,
        extract_entities=not args.no_entities
    )
    
    # Handle results
    if result["success"]:
        processed_doc = result["processed_doc"]
        
        print_success(f"Enhanced processing complete!")
        print(f"📄 Output: {result['output_path']}")
        print(f"⏱️ Processing time: {processed_doc.processing_time_ms}ms")
        print(f"📊 Words: {processed_doc.content_stats.get('word_count', 0):,}")
        print(f"🏷️ Tags: {len(processed_doc.all_tags)} total")
        
        if processed_doc.ai_summary:
            print(f"🤖 AI analysis: Summary + {len(processed_doc.ai_key_points)} key points")
        
        if processed_doc.extracted_entities:
            entity_counts = [len(items) for items in processed_doc.extracted_entities.values()]
            total_entities = sum(entity_counts)
            if total_entities > 0:
                print(f"🔍 Entities: {total_entities} extracted")
        
        # Move original if requested
        if args.move_original:
            try:
                moved_path = move_to_processed(args.input)
                print_success(f"Moved original to: {moved_path}")
            except Exception as e:
                print_error(f"Failed to move original: {e}")
        
        return 0
    else:
        print_error(f"Processing failed: {result.get('error', 'Unknown error')}")
        if result.get('processing_time_ms'):
            print(f"   Failed after: {result['processing_time_ms']}ms")
        return 1


if __name__ == "__main__":
    exit(main())
