class LLMError(RuntimeError):
    """Base error for anything that goes wrong at this abstraction layer."""


class LLMRateLimit(LLMError):
    """Raised when the provider indicates rate limiting or request timeout."""


class LLMAuthError(LLMError):
    """Raised when credentials are missing or invalid for a provider."""
