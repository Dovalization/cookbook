"""
Document processing pipeline for Cookbook.

Provides a standardized pipeline for processing various document types
with AI insights, content normalization, and metadata extraction.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from .core import ProcessingResult, ChatMessage
from .llm import LLM, LLMConfig
from .errors import LLMError
from .utils import get_logger

logger = get_logger(__name__)


@dataclass
class RawDocument:
    """
    Input document for processing pipeline.
    
    This represents unprocessed content with basic metadata
    that gets enriched through the DocumentProcessor.
    """
    # Core content
    content: str
    source_path: Optional[str] = None
    content_type: str = "text"  # text, pdf, html, markdown, etc.
    
    # Basic metadata
    title: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    
    # Processing hints
    suggested_tags: List[str] = field(default_factory=list)
    processing_notes: str = ""


@dataclass 
class ProcessedDocument:
    """
    Rich result from document processing pipeline.
    
    This contains comprehensive analysis including statistics,
    AI insights, extracted entities, and structured metadata.
    """
    # Basic processing info
    success: bool
    input_path: str
    output_path: Optional[str]
    error_message: Optional[str]
    processing_time_ms: int
    
    # Document analysis
    content_stats: Dict[str, Any] = field(default_factory=dict)
    ai_summary: Optional[str] = None
    ai_tags: List[str] = field(default_factory=list)
    ai_sentiment: Optional[str] = None
    ai_key_points: List[str] = field(default_factory=list)
    
    # Metadata and organization
    all_tags: List[str] = field(default_factory=list)  # Combined manual + AI tags
    content_hash: Optional[str] = None  # For deduplication
    processed_at: datetime = field(default_factory=datetime.now)
    
    # Relationships and context
    related_files: List[str] = field(default_factory=list)
    extracted_entities: Dict[str, List[str]] = field(default_factory=dict)  # dates, people, places
    
    def to_processing_result(self) -> ProcessingResult:
        """Convert to basic ProcessingResult for backward compatibility."""
        metadata = {
            "word_count": str(self.content_stats.get("word_count", 0)),
            "ai_enabled": str(self.ai_summary is not None),
            "tags_count": str(len(self.all_tags)),
            "has_summary": str(bool(self.ai_summary)),
            "sentiment": self.ai_sentiment or "unknown",
            "processing_time": str(self.processing_time_ms),
        }
        
        return ProcessingResult(
            success=self.success,
            input_path=self.input_path,
            output_path=self.output_path,
            error_message=self.error_message,
            processing_time_ms=self.processing_time_ms,
            metadata=metadata
        )


class DocumentProcessor:
    """
    Main document processing pipeline.
    
    Orchestrates content normalization, AI analysis, and insight extraction
    in a consistent, configurable way across all automation scripts.
    """
    
    def __init__(self, llm_config: Optional[LLMConfig] = None, enable_ai: bool = True):
        """
        Initialize document processor.
        
        Args:
            llm_config: LLM configuration (uses env defaults if None)
            enable_ai: Whether to enable AI processing
        """
        self.enable_ai = enable_ai
        self._llm = None
        self._llm_config = llm_config
        
        if enable_ai:
            try:
                self._llm_config = llm_config or LLMConfig.from_env()
                self._llm = LLM(self._llm_config)
                logger.info(f"AI processing enabled with {self._llm_config.provider}")
            except Exception as e:
                logger.warning(f"AI initialization failed, disabling: {e}")
                self.enable_ai = False
    
    def process(
        self, 
        raw_document: RawDocument,
        manual_tags: Optional[List[str]] = None,
        extract_entities: bool = True,
        summary_style: str = "bullet-point"
    ) -> ProcessedDocument:
        """
        Process document through the full pipeline.
        
        Args:
            raw_document: Document to process
            manual_tags: Additional tags to apply
            extract_entities: Whether to extract entities (dates, people, etc.)
            summary_style: Style for AI summary generation
            
        Returns:
            ProcessedDocument with full analysis
        """
        start_time = time.time()
        logger.info(f"Processing document: {raw_document.source_path or 'unknown'}")
        
        try:
            # Step 1: Content normalization and stats
            normalized_content = self._normalize_content(raw_document.content)
            content_stats = self._calculate_stats(normalized_content)
            content_hash = self._calculate_hash(normalized_content)
            
            # Step 2: AI analysis (if enabled)
            ai_summary = None
            ai_tags = []
            ai_sentiment = None
            ai_key_points = []
            
            if self.enable_ai and self._llm:
                try:
                    ai_results = self._run_ai_analysis(
                        normalized_content, 
                        summary_style,
                        raw_document.suggested_tags
                    )
                    ai_summary = ai_results.get("summary")
                    ai_tags = ai_results.get("tags", [])
                    ai_sentiment = ai_results.get("sentiment")
                    ai_key_points = ai_results.get("key_points", [])
                    
                    logger.info(f"AI analysis complete: {len(ai_tags)} tags, {len(ai_key_points)} key points")
                    
                except Exception as e:
                    logger.warning(f"AI analysis failed: {e}")
            
            # Step 3: Entity extraction (if requested)
            entities = {}
            if extract_entities:
                entities = self._extract_entities(normalized_content)
            
            # Step 4: Tag consolidation
            all_tags = self._consolidate_tags(
                manual_tags or [],
                raw_document.suggested_tags,
                ai_tags
            )
            
            # Step 5: Build result
            processing_time = int((time.time() - start_time) * 1000)
            
            processed_doc = ProcessedDocument(
                success=True,
                input_path=raw_document.source_path or "unknown",
                output_path=None,  # Set by caller after saving
                error_message=None,
                processing_time_ms=processing_time,
                content_stats=content_stats,
                ai_summary=ai_summary,
                ai_tags=ai_tags,
                ai_sentiment=ai_sentiment,
                ai_key_points=ai_key_points,
                all_tags=all_tags,
                content_hash=content_hash,
                extracted_entities=entities,
            )
            
            logger.info(f"Processing complete: {processing_time}ms")
            return processed_doc
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"Processing failed: {e}")
            
            return ProcessedDocument(
                success=False,
                input_path=raw_document.source_path or "unknown",
                output_path=None,
                error_message=str(e),
                processing_time_ms=processing_time,
            )
    
    def _normalize_content(self, content: str) -> str:
        """
        Normalize content for consistent processing.
        
        Args:
            content: Raw content string
            
        Returns:
            Normalized content
        """
        if not content:
            return ""
        
        # Basic normalization
        # - Consistent line endings
        # - Remove excessive whitespace
        # - Strip leading/trailing whitespace
        normalized = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive blank lines (more than 2)
        import re
        normalized = re.sub(r'\n{3,}', '\n\n', normalized)
        
        # Clean up spaces and tabs
        lines = []
        for line in normalized.split('\n'):
            # Convert tabs to spaces, remove trailing whitespace
            cleaned_line = line.expandtabs(4).rstrip()
            lines.append(cleaned_line)
        
        return '\n'.join(lines).strip()
    
    def _calculate_stats(self, content: str) -> Dict[str, Any]:
        """Calculate content statistics."""
        if not content:
            return {"word_count": 0, "char_count": 0, "line_count": 0}
        
        lines = content.split('\n')
        words = content.split()
        
        # Basic stats
        stats = {
            "word_count": len(words),
            "char_count": len(content),
            "char_count_no_spaces": len(content.replace(' ', '')),
            "line_count": len(lines),
            "non_empty_lines": len([line for line in lines if line.strip()]),
            "paragraph_count": len([line for line in lines if line.strip() and not line.startswith((' ', '\t'))]),
        }
        
        # Reading time estimate (average 200 words per minute)
        if stats["word_count"] > 0:
            stats["reading_time_minutes"] = max(1, stats["word_count"] // 200)
        else:
            stats["reading_time_minutes"] = 0
        
        # Content complexity hints
        if stats["word_count"] > 0:
            avg_word_length = stats["char_count_no_spaces"] / stats["word_count"]
            stats["avg_word_length"] = round(avg_word_length, 1)
            stats["complexity"] = "high" if avg_word_length > 6 else "medium" if avg_word_length > 4 else "low"
        else:
            stats["avg_word_length"] = 0
            stats["complexity"] = "unknown"
        
        return stats
    
    def _calculate_hash(self, content: str) -> str:
        """Calculate content hash for deduplication."""
        import hashlib
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def _run_ai_analysis(
        self, 
        content: str, 
        summary_style: str,
        suggested_tags: List[str]
    ) -> Dict[str, Any]:
        """Run AI analysis on content."""
        if not self._llm:
            return {}
        
        results = {}
        
        # Summary (for longer content)
        if len(content.split()) > 50:
            try:
                results["summary"] = self._llm.summarize(content, style=summary_style)
            except LLMError:
                pass
        
        # Tags
        try:
            ai_tags = self._llm.extract_tags(content, max_tags=7)
            results["tags"] = ai_tags
        except LLMError:
            pass
        
        # Sentiment
        try:
            results["sentiment"] = self._llm.analyze_sentiment(content)
        except LLMError:
            pass
        
        # Key points extraction (custom prompt)
        try:
            key_points = self._extract_key_points(content)
            results["key_points"] = key_points
        except LLMError:
            pass
        
        return results
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content using AI."""
        if not self._llm:
            return []
        
        # Truncate content for key point extraction
        from .core import MAX_CONTENT_LENGTH_FOR_AI
        truncated = content[:MAX_CONTENT_LENGTH_FOR_AI]
        
        messages = [
            {
                "role": "system",
                "content": "Extract the most important key points from the text. Return 3-7 concise bullet points, each on a new line starting with '-'. Focus on actionable insights, decisions, or critical information."
            },
            {"role": "user", "content": truncated}
        ]
        
        result = self._llm.chat(messages)
        
        # Parse bullet points
        points = []
        for line in result.text.split('\n'):
            line = line.strip()
            if line.startswith('-') or line.startswith('*') or line.startswith('•'):
                # Remove bullet and clean up
                point = line[1:].strip()
                if point and len(point) > 10:  # Ignore very short points
                    points.append(point)
        
        return points[:7]  # Max 7 key points
    
    def _extract_entities(self, content: str) -> Dict[str, List[str]]:
        """Extract entities (dates, people, etc.) from content."""
        # Basic regex-based entity extraction
        # In the future, this could use spaCy or similar NLP library
        import re
        from datetime import datetime
        
        entities = {
            "dates": [],
            "emails": [],
            "urls": [],
            "mentions": [],  # @username style mentions
            "phone_numbers": [],
        }
        
        # Date patterns (basic)
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or MM-DD-YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD or YYYY-MM-DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'  # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            entities["dates"].extend(matches)
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities["emails"] = re.findall(email_pattern, content)
        
        # URLs
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        entities["urls"] = re.findall(url_pattern, content)
        
        # @mentions
        mention_pattern = r'@[A-Za-z0-9_]+'
        entities["mentions"] = re.findall(mention_pattern, content)
        
        # Phone numbers (basic US format)
        phone_pattern = r'\b(?:\+1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
        entities["phone_numbers"] = re.findall(phone_pattern, content)
        
        # Remove duplicates and clean up
        for key in entities:
            entities[key] = list(set(entities[key]))
            entities[key] = [item.strip() for item in entities[key] if item.strip()]
        
        return entities
    
    def _consolidate_tags(
        self, 
        manual_tags: List[str], 
        suggested_tags: List[str], 
        ai_tags: List[str]
    ) -> List[str]:
        """
        Consolidate tags from different sources.
        
        Priority: manual > suggested > ai
        """
        all_tags = []
        
        # Add manual tags first (highest priority)
        all_tags.extend(manual_tags)
        
        # Add suggested tags if not already present
        for tag in suggested_tags:
            if tag.lower() not in [t.lower() for t in all_tags]:
                all_tags.append(tag)
        
        # Add AI tags if not already present
        for tag in ai_tags:
            if tag.lower() not in [t.lower() for t in all_tags]:
                all_tags.append(tag)
        
        # Clean up tags
        cleaned_tags = []
        for tag in all_tags:
            # Normalize tag
            clean_tag = tag.strip().lower()
            # Remove duplicates and empty tags
            if clean_tag and clean_tag not in cleaned_tags:
                cleaned_tags.append(clean_tag)
        
        return cleaned_tags[:10]  # Limit to 10 tags maximum


def create_raw_document_from_file(file_path: Path) -> RawDocument:
    """
    Create RawDocument from a file path.
    
    Convenience function for common use case of processing files.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Determine content type from extension
    content_type = "text"
    if file_path.suffix.lower() in ['.md', '.markdown']:
        content_type = "markdown"
    elif file_path.suffix.lower() in ['.html', '.htm']:
        content_type = "html"
    elif file_path.suffix.lower() == '.pdf':
        content_type = "pdf"
    
    # Extract title from filename or first line
    title = file_path.stem
    lines = content.split('\n')
    if lines and (lines[0].startswith('#') or len(lines[0]) < 100):
        # Use first line as title if it looks like a heading or is short
        first_line = lines[0].strip('#').strip()
        if first_line:
            title = first_line
    
    return RawDocument(
        content=content,
        source_path=str(file_path),
        content_type=content_type,
        title=title,
        created_at=datetime.fromtimestamp(file_path.stat().st_mtime)
    )
