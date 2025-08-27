"""
Pytest configuration and shared fixtures for Cookbook tests.

This module provides reusable fixtures and test utilities that are shared
across multiple test modules to reduce duplication and ensure consistency.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock
from typing import Dict, Any

from shared.llm.config import LLMConfig
from shared.llm.client import LLM
from shared.llm.adapters import LLMResult
from shared.document_processor import RawDocument, ProcessedDocument


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing file operations."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_text_content() -> str:
    """Sample text content for testing document processing."""
    return """# Test Document

This is a sample document for testing purposes.

## Key Features
- Python automation scripts
- AI-powered content analysis  
- File processing utilities
- Markdown output generation

The document contains technical content about software engineering,
automation, and artificial intelligence applications.

## Conclusion
This sample demonstrates various content types that the processing
pipeline should handle effectively."""


@pytest.fixture
def sample_raw_document(sample_text_content: str) -> RawDocument:
    """Sample RawDocument for testing."""
    return RawDocument(
        content=sample_text_content,
        source_path="/test/sample.txt",
        content_type="text",
        title="Test Document",
        suggested_tags=["testing", "sample"]
    )


@pytest.fixture
def mock_llm_config() -> LLMConfig:
    """Mock LLM configuration for testing."""
    return LLMConfig(
        provider="ollama",
        model="llama3",
        temperature=0.2,
        max_tokens=500,
        timeout_s=30,
        max_retries=2
    )


@pytest.fixture
def mock_llm_client() -> Mock:
    """Mock LLM client with realistic responses."""
    mock = Mock(spec=LLM)
    
    # Configure realistic mock responses
    mock.summarize.return_value = "This is a comprehensive summary of the test document, highlighting key features like Python automation, AI analysis, and file processing utilities."
    
    mock.extract_tags.return_value = ["python", "automation", "ai", "testing", "documentation"]
    
    mock.analyze_sentiment.return_value = "neutral"
    
    mock.chat.return_value = LLMResult(
        text="• Python automation and scripting capabilities\n• AI-powered content analysis features\n• File processing and markdown generation",
        raw={"message": {"content": "Key points response"}},
        provider="ollama",
        model="llama3",
        usage={"eval_count": 45}
    )
    
    return mock


@pytest.fixture
def mock_processed_document() -> ProcessedDocument:
    """Mock ProcessedDocument with realistic data."""
    return ProcessedDocument(
        success=True,
        input_path="/test/sample.txt",
        output_path="/output/sample_processed.md",
        error_message=None,
        processing_time_ms=250,
        content_stats={
            "word_count": 95,
            "char_count": 580,
            "line_count": 18,
            "reading_time_minutes": 1,
            "complexity": "medium"
        },
        ai_summary="Test document about Python automation and AI analysis.",
        ai_tags=["python", "automation", "ai"],
        ai_sentiment="neutral",
        ai_key_points=["Python automation", "AI analysis", "File processing"],
        all_tags=["python", "automation", "ai", "testing", "sample"],
        content_hash="abc123def456",
        extracted_entities={
            "technologies": ["Python", "AI"],
            "concepts": ["automation", "processing"]
        }
    )


@pytest.fixture
def mock_openai_response() -> Dict[str, Any]:
    """Mock OpenAI API response."""
    return {
        "choices": [{
            "message": {"content": "This is a mock OpenAI response."}
        }],
        "model": "gpt-4",
        "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18}
    }


@pytest.fixture
def mock_anthropic_response() -> Dict[str, Any]:
    """Mock Anthropic API response."""
    return {
        "content": [{
            "type": "text",
            "text": "This is a mock Anthropic response."
        }],
        "model": "claude-3-sonnet-20240229",
        "usage": {"input_tokens": 12, "output_tokens": 9}
    }


@pytest.fixture
def mock_ollama_response() -> Dict[str, Any]:
    """Mock Ollama API response."""
    return {
        "message": {"content": "This is a mock Ollama response."},
        "model": "llama3",
        "eval_count": 35,
        "done": True
    }


@pytest.fixture
def sample_files(temp_dir: Path) -> Dict[str, Path]:
    """Create sample files for testing scripts."""
    files = {}
    
    # Simple text file
    files["simple"] = temp_dir / "simple.txt"
    files["simple"].write_text("This is a simple test file.")
    
    # Markdown file
    files["markdown"] = temp_dir / "document.md"
    files["markdown"].write_text("""# Sample Document
    
This is a markdown document for testing.

## Features
- Bullet points
- Headers
- Text content
""")
    
    # Long text file (for AI processing)
    files["long"] = temp_dir / "long_content.txt"
    long_content = """
This is a longer document that should trigger AI processing.
""" + " ".join(["Word"] * 100)  # 100+ words to trigger AI summarization
    files["long"].write_text(long_content)
    
    # Empty file
    files["empty"] = temp_dir / "empty.txt"
    files["empty"].write_text("")
    
    return files


@pytest.fixture
def environment_vars() -> Dict[str, str]:
    """Sample environment variables for testing configuration."""
    return {
        "LLM_PROVIDER": "ollama",
        "LLM_MODEL": "llama3",
        "LLM_TEMPERATURE": "0.2",
        "LLM_MAX_TOKENS": "500",
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "ENABLE_AI_PROCESSING": "true",
        "LOG_LEVEL": "INFO"
    }


@pytest.fixture
def mock_config(temp_dir: Path) -> Mock:
    """Mock global configuration object."""
    mock = Mock()
    mock.OUTPUT_PATH = temp_dir / "output"
    mock.BACKUP_PATH = temp_dir / "backup"
    mock.LOG_LEVEL = "INFO"
    mock.ENABLE_AI_PROCESSING = True
    return mock


# Test helper functions

def create_test_file(path: Path, content: str) -> Path:
    """Helper function to create a test file with content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    return path


def assert_file_exists_with_content(path: Path, expected_content: str = None) -> None:
    """Helper function to assert file exists and optionally check content."""
    assert path.exists(), f"Expected file {path} to exist"
    if expected_content is not None:
        actual_content = path.read_text(encoding='utf-8')
        assert actual_content == expected_content, f"File content mismatch in {path}"


def assert_markdown_structure(content: str) -> None:
    """Helper function to assert markdown content has expected structure."""
    assert "# " in content, "Expected markdown to have headers"
    assert "**" in content or "_" in content, "Expected markdown to have emphasis"
    assert content.strip(), "Expected non-empty markdown content"