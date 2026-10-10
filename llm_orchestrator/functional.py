"""Pure preparation and post-processing functions."""

from llm_orchestrator.models.requests import LlmRequest


def estimate_tokens(text: str) -> int:
    """Estimate tokens from whitespace-separated words for demo metrics."""
    return len(text.split()) * 2


def request_summary(request: LlmRequest) -> dict[str, str]:
    """Return safe metadata suitable for logs without returning prompt text."""
    return {
        "request_id": request.request_id,
        "provider_name": request.provider_name,
        "operation": request.operation.value,
    }
