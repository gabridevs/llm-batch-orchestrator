"""Domain exceptions used by the LLM orchestrator."""


class ProviderError(Exception):
    """Base exception for all provider-related failures."""


class TransientProviderError(ProviderError):
    """Error that may succeed if the request is retried."""


class PermanentProviderError(ProviderError):
    """Error that should not be retried."""


class RateLimitError(TransientProviderError):
    """Raised when a provider temporarily rejects excess traffic."""


class ProviderTimeoutError(TransientProviderError):
    """Raised when a provider response takes too long."""


class InvalidRequestError(PermanentProviderError):
    """Raised when a provider receives an invalid request."""


class ProviderNotFoundError(PermanentProviderError):
    """Raised when a requested provider is not registered."""
