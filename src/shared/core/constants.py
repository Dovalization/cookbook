"""
Constants used throughout Cookbook.
"""

# ============================================================================
# LLM Defaults
# ============================================================================

# Default provider settings
DEFAULT_PROVIDER = "ollama"
DEFAULT_MODEL = "llama3"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = None
DEFAULT_TIMEOUT_S = 60
DEFAULT_MAX_RETRIES = 3

# Provider-specific defaults
OPENAI_BASE_URL = "https://api.openai.com"
ANTHROPIC_BASE_URL = "https://api.anthropic.com"  
ANTHROPIC_VERSION = "2023-06-01"
OLLAMA_BASE_URL = "http://localhost:11434"

# ============================================================================
# File Processing
# ============================================================================

# Default directories
DEFAULT_INBOX = "./inbox"
DEFAULT_OUTPUT = "./output"
DEFAULT_BACKUP = "./backup"

# File processing limits
MAX_FILE_SIZE_MB = 100
MAX_CONTENT_LENGTH_FOR_AI = 2000  # chars for summarization
MAX_CONTENT_LENGTH_FOR_TAGS = 1000  # chars for tag extraction

# ============================================================================
# Logging
# ============================================================================

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
