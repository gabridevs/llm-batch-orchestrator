"""Pure functions for orchestration metrics."""

from llm_orchestrator.models.reports import ExecutionMetrics
from llm_orchestrator.models.results import RequestResult, RequestStatus


def build_execution_metrics(
    results: tuple[RequestResult, ...],
    total_elapsed_seconds: float,
) -> ExecutionMetrics:
    """Calculate aggregate metrics without mutating results or external state."""
    successful_requests = sum(
        result.status == RequestStatus.SUCCESS for result in results
    )
    total_retries = sum(result.attempts - 1 for result in results)
    estimated_tokens = sum(result.estimated_tokens for result in results)
    return ExecutionMetrics(
        total_requests=len(results),
        successful_requests=successful_requests,
        failed_requests=len(results) - successful_requests,
        total_retries=total_retries,
        total_elapsed_seconds=total_elapsed_seconds,
        estimated_tokens=estimated_tokens,
    )
