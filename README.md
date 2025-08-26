# Cookbook 🍳

A collection of automation recipes for streamlining personal workflows, knowledge management, and everyday digital tasks in the era of artificial intelligence.

⚠️ This project is a work in progress, some recipes may be incomplete, broken, or not fully tested. That said, contributions are welcome! ⚠️

## What is Cookbook?

Cookbook is a personal toolkit of Python scripts that automate the tedious parts of work. Each "recipe" solves a specific problem - transcribing audio, scraping web content, organizing files, or connecting different parts of your digital workflow.

Think of it as your automation catalog: individual recipes that work standalone, but can be combined to create more complex workflows.

## Personal Motivation
This project exists because I got tired of doing the same manual tasks over and over again. As someone with ADHD, I need external systems to handle the routine stuff so my brain can focus on the important stuff.
Every script in this collection solves a real friction point in my daily workflow:

- **Meeting transcripts** - I record everything but never had time to review what was said.
- **Web research** - Bookmarking articles I'd never read again in a useful format.
- **File organization** - Opinionated file structure designed for productivity, quick capture and retrieval.
- **Context switching** - Keep track of evolving requirements and tasks and minimize distractions.

The goal isn't to automate everything, but to automate the annoying things that drain mental energy without adding value. I'm designing each recipe to work with my natural workflow, not how productivity apps think I should work.

## Quick Start

```bash
git clone https://github.com/dovalization/cookbook.git
cd cookbook
pip install -r requirements.txt
cp .env.example .env  # Configure your settings

# Try a recipe
python -m scripts.scrape_webpage https://example.com/article
```

## Repository Structure

```
cookbook/
├── scripts/           # Individual automation recipes
├── workflows/         # Combined recipes for complex tasks
├── shared/           # Common utilities and helpers
├── examples/         # Sample inputs and usage examples
└── tests/           # Keep your recipes working
```

## Available Recipes

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

## Workflows (Recipe Combinations)

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
# Obsidian vault path
OBSIDIAN_VAULT_PATH="/path/to/your/vault"

# API keys (optional)
OPENAI_API_KEY="your-key-here"

# Storage locations
INBOX_PATH="/path/to/inbox"
PROCESSED_PATH="/path/to/processed"
```

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
# Transcribe a meeting recording
python -m scripts.transcribe_audio meeting.wav

# Scrape an article for research
python -m scripts.scrape_webpage https://blog.example.com/post --tags research,ai

# Summarize any text file
python -m scripts.summarize_content document.txt
```

### Workflow Chains
```bash
# Full meeting processing pipeline
python -m workflows.meeting_flow recording.wav \
  --transcribe \
  --summarize \
  --create-note \
  --extract-action-items

# Research workflow
python -m workflows.research_flow https://paper.arxiv.org/1234 \
  --summarize \
  --extract-concepts \
  --suggest-tags
```

## Integration Points

Cookbook plays nicely with:
- **Obsidian** - Auto-creates notes with proper frontmatter and tags
- **Local LLMs** - Uses OLLAMA for privacy-first AI processing  
- **File watchers** - Can monitor folders for automatic processing
- **Git hooks** - Trigger workflows on repository changes
- **Homelabs** - Designed to run on personal infrastructure

## Development

### Adding New Recipes

1. Create your script in `scripts/`
2. Follow the template pattern
3. Add shared utilities to `shared/` if needed
4. Write tests in `tests/`
5. Update this README

### Testing Recipes
```bash
# Test individual scripts
python -m pytest tests/test_script_name.py

# Test workflows
python -m pytest tests/test_workflows.py

# Run all tests
python -m pytest
```

### Shared Utilities

Common functionality lives in `shared/`:
- `obsidian.py` - Vault operations (create notes, update metadata)
- `storage.py` - SQLite helpers for tracking processed items
- `config.py` - Configuration management
- `utils.py` - General helpers (file operations, text processing)

## Philosophy

- **One Recipe, One Job** - Each script solves exactly one problem well.
- **Composable** - Scripts can be chained together for complex workflows.
- **Local First** - Runs on your infrastructure, your data stays yours.
- **ADHD Friendly** - Reduces cognitive load by automating tedious tasks.
- **Iterative** - Start simple, evolve based on actual usage.

## Requirements

- Python 3.9+
- See `requirements.txt` for package dependencies
- Optional: OLLAMA for local AI processing
- Optional: FFmpeg for audio/video processing

## License

Personal use. Feel free to fork and adapt for your own automation needs.

---

*Cookbook: Because good automation, like good cooking, starts with having the right recipes.*