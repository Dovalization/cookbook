# Cookbook 🍳

A collection of automation recipes for streamlining personal workflows, knowledge management, and everyday digital tasks in the era of artificial intelligence.

*Cookbook: Because good automation, like good cooking, starts with having the right recipes.*

⚠️ This project is a work in progress, some recipes may be incomplete, broken, or not fully tested. That said, contributions are welcome! ⚠️

## What is Cookbook?

Cookbook is a personal toolkit of Python scripts that automate the tedious parts of work. Each "recipe" solves a specific problem - transcribing audio, scraping web content, organizing files, or connecting different parts of your digital workflow.

Think of it as your automation catalog: individual recipes that work standalone, but can be combined to create more complex workflows.

## Personal Motivation

This project exists because I got tired of doing the same manual tasks over and over again. As someone with ADHD, I need external systems to handle the routine tasks so my brain can focus on the important stuff.

Every script in this collection solves a real friction point in my daily workflow:

- **Meeting transcripts** - I record everything but never had time to review what was said.
- **Web research** - Bookmarking articles I'd never read again in a useful format.
- **File organization** - Opinionated file structure designed for productivity, quick capture and retrieval.
- **Context switching** - Keep track of evolving requirements and tasks and minimize distractions.

The goal isn't to automate everything, but to automate the annoying things that drain mental energy without adding value. I'm designing each recipe to work with my natural workflow, not how productivity apps think I should work.

## Technical Principles

### Keep It Simple
- Each script solves exactly one problem
- Prefer composition over complexity
- Add features based on actual usage, not speculation

### Local First
- Work offline when possible
- User owns their data
- Privacy-first approach with local LLMs when needed

### Gradual Adoption
- Each phase builds on the previous
- Scripts work independently before integration
- Easy to disable/modify any component

### ADHD-Friendly Design
- Reduce cognitive load, don't add it
- Automate the boring parts, surface the important parts
- Clear feedback on what's happening

## Getting Started

### Quick Start

```bash
git clone https://github.com/dovalization/cookbook.git
cd cookbook
pip install -r requirements.txt
cp .env.example .env  # Configure your settings

# Try a recipe
python -m scripts.example_script input.txt
```

### Technology Stack
- **Backend**: Python with FastAPI for future dashboard API
- **Frontend**: Next.js with TypeScript (future phases)
- **Database**: SQLite for development/simple deployments
- **Authentication**: OAuth 2.0 with secure token storage
- **Development**: Docker + Docker Compose
- **Testing**: pytest with mocking for APIs

### Development Philosophy
- **Build what you need, when you need it**
- **Start with manual processes, then automate the painful parts**  
- **Every script should solve a real problem you're actually having**
- **Perfection is the enemy of automation**

## Repository Structure

```
cookbook/
├── scripts/           # Individual automation recipes
├── workflows/         # Combined recipes for complex tasks
├── shared/           # Common utilities and helpers
├── examples/         # Sample inputs and usage examples
└── tests/           # Keep your recipes working
```

## Current Status

### ✅ What We Have (Phase 1.1 + 1.2 Complete!)
- **LLM Abstraction Layer**: Production-ready AI integration with OpenAI, Anthropic, and Ollama
- **Content Processing Pipeline**: Rich analysis with entity extraction, statistics, and AI insights  
- **Enhanced File Utilities**: Smart deduplication, metadata extraction, and organized output
- **Working Automation Scripts**: Multiple text processors with graceful AI fallback
- **Comprehensive Testing**: Validation scripts and integration tests
- **ADHD-Friendly Design**: Consistent patterns that reduce cognitive load

### 🔄 Next Phase (Phase 2: Storage & Persistence)
- **SQLite Integration**: Track processed items and enable search capabilities
- **Deduplication System**: Prevent reprocessing using content hashing
- **Processing History**: Query past processing results and analytics
- **Database Schema**: Migrations and structured storage for ProcessedItems

## Planned Recipes

### 🎵 Audio & Content
- **transcribe_audio** - Turn audio files into text transcripts
- **summarize_content** - Extract key points from any text
- **extract_audio** - Pull audio from video files

### 🌐 Web & Research  
- **scrape_webpage** - Convert web articles to clean markdown
- **archive_thread** - Save Twitter/social media threads
- **fetch_documentation** - Download and organize technical docs

### 📄 File Processing
- **extract_pdf_text** - Pull text from PDF documents
- **ocr_screenshots** - Make image text searchable
- **organize_inbox** - Auto-sort files into proper folders

### 🔧 System Maintenance
- **check_vault_health** - Find broken links and orphaned files
- **backup_workspace** - Sync important data to multiple locations
- **clean_duplicates** - Find and remove duplicate files

## Future Workflows (Recipe Combinations)

### Meeting Processor
Audio file → Transcription → Summary → Organized notes
```bash
python -m workflows.meeting_flow input.wav --auto-summarize
```

### Research Assistant  
URL → Scraped content → Summary → Linked notes
```bash
python -m workflows.research_flow https://interesting-article.com
```

### Content Pipeline
Any input → Processed → Categorized → Stored → Searchable
```bash
python -m workflows.content_pipeline input.* --auto-tag
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# File processing paths
INBOX_PATH="./inbox"
OUTPUT_PATH="./output"
BACKUP_PATH="./backup"

# LLM Configuration
OPENAI_API_KEY=""           # For OpenAI models
ANTHROPIC_API_KEY=""        # For Claude models
OLLAMA_BASE_URL="http://localhost:11434"  # For local models

# Processing settings
DEFAULT_LLM_PROVIDER="ollama"  # ollama, openai, or anthropic
ENABLE_AI_PROCESSING="true"     # false to disable AI features

# System
LOG_LEVEL="INFO"
DATABASE_PATH="./cookbook.db"
```

## Development Roadmap

For detailed development phases and milestones, see [ROADMAP.md](ROADMAP.md).

### ✅ Phase 1.1 + 1.2 Complete!
1. ✅ **LLM Abstraction Layer** - Production-ready with 3 provider support
2. ✅ **Content Processing Pipeline** - Rich analysis with entities and statistics
3. ✅ **Enhanced File Utilities** - Smart output handling and deduplication
4. ✅ **Working Automation Scripts** - Multiple text processors with AI integration
5. ✅ **Comprehensive Testing** - Validation and demo scripts

### 🔄 Next Steps (Phase 2: Storage & Persistence)
1. **SQLite Database Integration** - Store ProcessedItem objects
2. **Content Deduplication** - Use SHA-256 hashing to prevent reprocessing
3. **Search and Retrieval** - Query processed content by tags, entities, dates
4. **Processing Analytics** - Track automation usage and effectiveness

## Recipe Template

Each script follows a consistent pattern:

```python
#!/usr/bin/env python3
"""
Recipe: Short description
Purpose: What problem this solves
Input: What it expects
Output: What it produces
"""

def main(input_path: str, **kwargs):
    # Recipe logic here
    pass

if __name__ == "__main__":
    # CLI interface
    pass
```

## Usage Examples

### Standalone Scripts
```bash
# Transcribe a meeting recording (future)
python -m scripts.transcribe_audio meeting.wav

# Scrape an article for research (future)
python -m scripts.scrape_webpage https://blog.example.com/post --tags research,ai

# Summarize any text file (future)
python -m scripts.summarize_content document.txt
```

### Current Working Scripts
```bash
# Basic text processing with file metadata
python -m scripts.example_script input.txt --move-original

# AI-powered text processing with insights
python -m scripts.ai_text_processor input.txt --tags research,important

# Enhanced processing with entities and rich output
python -m scripts.enhanced_text_processor input.txt --summary-style detailed
```

## Integration Philosophy

Cookbook is designed to work with your existing tools:
- **Local LLMs** - Uses OLLAMA for privacy-first AI processing  
- **File watchers** - Can monitor folders for automatic processing
- **Git hooks** - Trigger workflows on repository changes
- **Homelabs** - Designed to run on personal infrastructure
- **Future**: Slack, Google Workspace, Jira integration

## Development

### Adding New Recipes

1. Create your script in `scripts/`
2. Follow the template pattern
3. Add shared utilities to `shared/` if needed
4. Write tests in `tests/`
5. Update this README

### Running Tests
```bash
# Test individual scripts (when available)
python -m pytest tests/test_script_name.py

# Test workflows (when available)
python -m pytest tests/test_workflows.py

# Run all tests
python -m pytest
```

### Docker Development (Coming Soon)
```bash
# Build and run development environment
docker-compose up --build

# Run tests in container
docker-compose run cookbook pytest
```

## Requirements

- Python 3.9+
- See `requirements.txt` for package dependencies
- Optional: Docker for containerized development
- Optional: OLLAMA for local AI processing
- Optional: FFmpeg for audio/video processing

## License

Personal use. Feel free to fork and adapt for your own automation needs.

---

*Remember: The best automation is the one you actually use. Start simple, solve real problems, and let the system grow organically based on your actual needs.*