# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_document_processor.py

# Run tests with verbose output
pytest -v
```

### Code Quality
```bash
# Format code with black
black src/

# Check code style with flake8
flake8 src/

# Format specific files
black src/shared/llm/client.py
```

### Running Scripts
```bash
# Basic text processing
python -m scripts.example_script input.txt --move-original

# AI-powered text processing
python -m scripts.ai_text_processor input.txt --tags research,important

# Enhanced processing with entities
python -m scripts.enhanced_text_processor input.txt --summary-style detailed
```

### Package Management
```bash
# Install dependencies
pip install -r requirements.txt

# Install with optional dependencies
pip install -e .[dev,ai,audio]

# Build package
python -m build
```

## Architecture Overview

### Core Components

**LLM Abstraction Layer** (`src/shared/llm/`)
- `client.py`: Main LLM client with provider abstraction (OpenAI, Anthropic, Ollama)
- `adapters.py`: Provider-specific implementations
- `config.py`: Configuration management with environment variable support
- `http_client.py`: HTTP client with retry logic and error handling

**Document Processing Pipeline** (`src/shared/document_processor.py`)
- `RawDocument`: Input document with basic metadata
- `ProcessedDocument`: Rich output with AI insights, entities, statistics
- `DocumentProcessor`: Main processing engine with AI integration
- Supports content analysis, entity extraction, and summarization

**Shared Utilities** (`src/shared/`)
- `core/`: Types, constants, and core data structures
- `utils/`: File handling, logging, CLI utilities
- `errors.py`: Custom exception hierarchy
- `config.py`: Global configuration management

### Script Architecture

All scripts follow a consistent pattern:
- Take input files/content
- Process using shared utilities and LLM integration  
- Generate structured output with metadata
- Support tags, move operations, and batch processing
- Use `shared.utils.setup_logging()` for consistent logging
- Follow the template in `scripts/example_script.py`

### Data Flow

1. **Input**: Text files, documents, or content
2. **Processing**: 
   - Content normalization and validation
   - AI analysis (if enabled) with provider fallback
   - Entity extraction and metadata enrichment
   - Statistics generation
3. **Output**: 
   - Structured markdown with metadata
   - Rich analysis results (entities, insights, summaries)
   - Original content preservation
   - Organized file management

### Configuration

Environment variables in `.env`:
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`: API credentials
- `OLLAMA_BASE_URL`: Local LLM endpoint (default: http://localhost:11434)
- `DEFAULT_LLM_PROVIDER`: ollama, openai, or anthropic
- `ENABLE_AI_PROCESSING`: Enable/disable AI features
- `LOG_LEVEL`: Logging verbosity

### Testing Strategy

- Tests located in `src/tests/`
- Uses pytest framework
- Includes integration tests for LLM providers
- Mock external API calls for reliability
- Test fixtures in `tests/fixtures/`
- Sample data in `tests/samples/`

### Project Structure

- `src/scripts/`: Individual automation recipes
- `src/workflows/`: Combined recipes for complex tasks (future)
- `src/shared/`: Common utilities and libraries
- `src/tests/`: Test suite with fixtures and samples
- `docs/`: Documentation and development logs
- `requirements.txt`: Python dependencies
- `pyproject.toml`: Package configuration with optional dependencies

## Key Patterns

- **Provider Abstraction**: LLM client supports multiple providers with unified interface
- **Graceful Degradation**: AI features fail gracefully when unavailable
- **Content Length Limits**: Automatic truncation for API limits (defined in `core/constants.py`)
- **Structured Output**: All processors return `ProcessedDocument` with rich metadata
- **Error Handling**: Custom exceptions with provider-specific error mapping
- **Logging**: Consistent logging setup across all modules