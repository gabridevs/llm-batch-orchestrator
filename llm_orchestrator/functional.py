"""Pure preparation and post-processing functions."""

from collections.abc import Iterable

from llm_orchestrator.models.requests import BatchRequest, LlmRequest
from llm_orchestrator.models.results import RequestResult, RequestStatus


def prepare_batch(requests: Iterable[LlmRequest]) -> BatchRequest:
    """Build an immutable validated batch without mutating the input iterable."""
    return BatchRequest(requests=tuple(requests))


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


def partition_results(
    results: tuple[RequestResult, ...],
) -> tuple[tuple[RequestResult, ...], tuple[RequestResult, ...]]:
    """Return immutable success and failure groups while preserving their order."""
    successful_results = tuple(
        result for result in results if result.status == RequestStatus.SUCCESS
    )
    failed_results = tuple(
        result for result in results if result.status == RequestStatus.FAILURE
    )
    return successful_results, failed_results
