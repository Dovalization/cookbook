"""
Unit tests for document processor with mocked LLM client.

Tests the document processing pipeline without making actual AI API calls.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from shared.document_processor import (
    DocumentProcessor,
    RawDocument,
    ProcessedDocument
)
from shared.llm.config import LLMConfig
from shared.llm.client import LLM
from shared.llm.adapters import LLMResult
from shared.errors import LLMError


class TestRawDocument:
    """Test suite for RawDocument data class."""

    def test_raw_document_creation_minimal(self) -> None:
        """Test creating RawDocument with minimal data."""
        doc = RawDocument(content="Hello world")
        
        assert doc.content == "Hello world"
        assert doc.source_path is None
        assert doc.content_type == "text"
        assert doc.title is None
        assert doc.author is None
        assert doc.created_at is None
        assert doc.suggested_tags == []
        assert doc.processing_notes == ""

    def test_raw_document_creation_full(self) -> None:
        """Test creating RawDocument with all fields."""
        created_at = datetime(2024, 1, 15, 10, 30)
        doc = RawDocument(
            content="Test content",
            source_path="/path/to/file.txt",
            content_type="markdown",
            title="Test Document",
            author="Test Author",
            created_at=created_at,
            suggested_tags=["tag1", "tag2"],
            processing_notes="Test notes"
        )
        
        assert doc.content == "Test content"
        assert doc.source_path == "/path/to/file.txt"
        assert doc.content_type == "markdown"
        assert doc.title == "Test Document"
        assert doc.author == "Test Author"
        assert doc.created_at == created_at
        assert doc.suggested_tags == ["tag1", "tag2"]
        assert doc.processing_notes == "Test notes"


class TestProcessedDocument:
    """Test suite for ProcessedDocument data class."""

    def test_processed_document_creation(self) -> None:
        """Test creating ProcessedDocument."""
        processed = ProcessedDocument(
            success=True,
            input_path="/input/file.txt",
            output_path="/output/file.md",
            error_message=None,
            processing_time_ms=150,
            ai_summary="This is a summary",
            ai_tags=["python", "automation"],
            all_tags=["python", "automation", "manual"]
        )
        
        assert processed.success is True
        assert processed.input_path == "/input/file.txt"
        assert processed.output_path == "/output/file.md"
        assert processed.error_message is None
        assert processed.processing_time_ms == 150
        assert processed.ai_summary == "This is a summary"
        assert processed.ai_tags == ["python", "automation"]
        assert processed.all_tags == ["python", "automation", "manual"]

    def test_to_processing_result(self) -> None:
        """Test conversion to ProcessingResult format."""
        processed = ProcessedDocument(
            success=True,
            input_path="/test/file.txt",
            output_path="/test/output.md",
            error_message=None,
            processing_time_ms=200,
            content_stats={"word_count": 100},
            ai_summary="Test summary",
            all_tags=["tag1", "tag2"],
            ai_sentiment="positive"
        )
        
        result = processed.to_processing_result()
        
        assert result["success"] is True
        assert result["input_path"] == "/test/file.txt"
        assert result["output_path"] == "/test/output.md"
        assert result["error_message"] is None
        assert result["processing_time_ms"] == 200
        
        # Check metadata conversion
        metadata = result["metadata"]
        assert metadata["word_count"] == "100"
        assert metadata["ai_enabled"] == "True"
        assert metadata["tags_count"] == "2"
        assert metadata["has_summary"] == "True"
        assert metadata["sentiment"] == "positive"
        assert metadata["processing_time"] == "200"


class TestDocumentProcessor:
    """Test suite for DocumentProcessor functionality."""

    @pytest.fixture
    def sample_content(self) -> str:
        """Sample content for testing."""
        return """This is a test document.

It has multiple paragraphs with different content.
Some technical terms like Python, API, and automation.

The document discusses software engineering practices."""

    @pytest.fixture
    def mock_llm_config(self) -> LLMConfig:
        """Mock LLM configuration."""
        return LLMConfig(
            provider="ollama",
            model="llama3",
            temperature=0.2
        )

    @pytest.fixture
    def mock_llm(self) -> Mock:
        """Mock LLM client."""
        mock = Mock(spec=LLM)
        mock.summarize.return_value = "This is a test document about software engineering."
        mock.extract_tags.return_value = ["python", "automation", "engineering"]
        mock.analyze_sentiment.return_value = "neutral"
        mock.chat.return_value = LLMResult(
            text="Key point 1\nKey point 2",
            raw={},
            provider="ollama",
            model="llama3"
        )
        return mock

    def test_processor_initialization_with_ai_enabled(self, mock_llm_config: LLMConfig) -> None:
        """Test processor initialization with AI enabled."""
        with patch('shared.document_processor.LLMConfig.from_env', return_value=mock_llm_config):
            with patch('shared.document_processor.LLM') as mock_llm_class:
                processor = DocumentProcessor(enable_ai=True)
                
                assert processor.enable_ai is True
                mock_llm_class.assert_called_once_with(mock_llm_config)

    def test_processor_initialization_with_ai_disabled(self) -> None:
        """Test processor initialization with AI disabled."""
        processor = DocumentProcessor(enable_ai=False)
        
        assert processor.enable_ai is False
        assert processor._llm is None

    def test_processor_initialization_ai_fails_gracefully(self) -> None:
        """Test processor handles AI initialization failure gracefully."""
        with patch('shared.document_processor.LLMConfig.from_env', side_effect=Exception("No config")):
            processor = DocumentProcessor(enable_ai=True)
            
            assert processor.enable_ai is False
            assert processor._llm is None

    def test_process_without_ai(self, sample_content: str) -> None:
        """Test document processing without AI."""
        processor = DocumentProcessor(enable_ai=False)
        
        raw_doc = RawDocument(
            content=sample_content,
            source_path="/test/file.txt",
            suggested_tags=["manual-tag"]
        )
        
        result = processor.process(raw_doc, manual_tags=["additional-tag"])
        
        assert result.success is True
        assert result.input_path == "/test/file.txt"
        assert result.ai_summary is None
        assert result.ai_tags == []
        assert result.ai_sentiment is None
        assert result.all_tags == ["additional-tag", "manual-tag"]
        assert result.content_hash is not None
        assert len(result.content_hash) == 16
        
        # Check content stats
        stats = result.content_stats
        assert stats["word_count"] > 0
        assert stats["char_count"] > 0
        assert stats["line_count"] > 0

    def test_process_with_ai(self, sample_content: str, mock_llm: Mock) -> None:
        """Test document processing with AI analysis."""
        processor = DocumentProcessor(enable_ai=True)
        processor._llm = mock_llm
        
        # Use longer content to ensure AI summary is generated (>50 words)
        long_content = sample_content + " " + " ".join(["Additional"] * 50) + " content for AI processing."
        
        raw_doc = RawDocument(
            content=long_content,
            source_path="/test/file.txt"
        )
        
        result = processor.process(raw_doc, summary_style="detailed")
        
        assert result.success is True
        assert result.ai_summary == "This is a test document about software engineering."
        assert result.ai_tags == ["python", "automation", "engineering"]
        assert result.ai_sentiment == "neutral"
        
        # Verify LLM methods were called
        mock_llm.summarize.assert_called_once()
        mock_llm.extract_tags.assert_called_once()
        mock_llm.analyze_sentiment.assert_called_once()

    def test_process_ai_analysis_fails_gracefully(self, sample_content: str, mock_llm: Mock) -> None:
        """Test that AI analysis failures don't crash processing."""
        processor = DocumentProcessor(enable_ai=True)
        processor._llm = mock_llm
        
        # Make AI methods fail
        mock_llm.summarize.side_effect = LLMError("AI failed")
        mock_llm.extract_tags.side_effect = LLMError("AI failed")
        mock_llm.analyze_sentiment.side_effect = LLMError("AI failed")
        
        raw_doc = RawDocument(content=sample_content)
        result = processor.process(raw_doc)
        
        # Processing should still succeed
        assert result.success is True
        assert result.ai_summary is None
        assert result.ai_tags == []
        assert result.ai_sentiment is None

    def test_normalize_content_basic(self) -> None:
        """Test basic content normalization."""
        processor = DocumentProcessor(enable_ai=False)
        
        content = "  Hello world  \r\n\r\nSecond line\t  \r\n  "
        normalized = processor._normalize_content(content)
        
        assert normalized == "Hello world\n\nSecond line"

    def test_calculate_stats_comprehensive(self) -> None:
        """Test comprehensive content statistics calculation."""
        processor = DocumentProcessor(enable_ai=False)
        
        content = """First paragraph with some words.

Second paragraph.
Third line."""
        
        stats = processor._calculate_stats(content)
        
        # Count actual words: First, paragraph, with, some, words, Second, paragraph, Third, line = 9 words
        assert stats["word_count"] == 9
        assert stats["char_count"] == len(content)
        assert stats["line_count"] == 4
        assert stats["non_empty_lines"] == 3
        assert stats["reading_time_minutes"] == 1  # 8 words < 200, so minimum 1
        assert isinstance(stats["avg_word_length"], float)
        assert stats["complexity"] in ["low", "medium", "high"]

    def test_calculate_hash_consistency(self) -> None:
        """Test content hash calculation is consistent."""
        processor = DocumentProcessor(enable_ai=False)
        
        content = "Test content for hashing"
        hash1 = processor._calculate_hash(content)
        hash2 = processor._calculate_hash(content)
        
        assert hash1 == hash2
        assert len(hash1) == 16
        assert hash1.isalnum()

    @patch('time.time')
    def test_processing_time_calculation(self, mock_time: Mock) -> None:
        """Test processing time calculation with mocked time."""
        processor = DocumentProcessor(enable_ai=False)
        
        # Mock time progression: start=1.0, end=1.5 (500ms)
        mock_time.side_effect = [1.0, 1.5]
        
        raw_doc = RawDocument(content="Test")
        result = processor.process(raw_doc)
        
        assert result.processing_time_ms == 500