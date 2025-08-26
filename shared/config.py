"""Configuration management for Cookbook."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Central configuration for all Cookbook scripts."""
    
    # Paths
    INBOX_PATH = Path(os.getenv("INBOX_PATH", "./inbox"))
    OUTPUT_PATH = Path(os.getenv("OUTPUT_PATH", "./output"))
    BACKUP_PATH = Path(os.getenv("BACKUP_PATH", "./backup"))
    
    # Database
    DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "./cookbook.db"))
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Local LLM
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = Path(os.getenv("LOG_FILE", "./cookbook.log"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        # Create directories if they don't exist
        for path in [cls.INBOX_PATH, cls.OUTPUT_PATH, cls.BACKUP_PATH]:
            path.mkdir(parents=True, exist_ok=True)
        
        return True

# Global config instance
config = Config()