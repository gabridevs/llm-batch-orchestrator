"""Batch report and execution metric models."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from llm_orchestrator.models.results import RequestResult, RequestStatus


class ExecutionMetrics(BaseModel):
    """Summarize one orchestration run."""

    model_config = ConfigDict(frozen=True)

    total_requests: int = Field(ge=0)
    successful_requests: int = Field(ge=0)
    failed_requests: int = Field(ge=0)
    total_retries: int = Field(ge=0)
    total_elapsed_seconds: float = Field(ge=0)
    estimated_tokens: int = Field(ge=0)


class BatchReport(BaseModel):
    """Contain ordered per-request results and aggregate metrics."""

    model_config = ConfigDict(frozen=True)

    strategy_name: str
    results: tuple[RequestResult, ...]
    metrics: ExecutionMetrics

    @model_validator(mode="after")
    def validate_metrics_match_results(self) -> "BatchReport":
        """Ensure aggregate counts agree with result statuses."""
        actual_successes = sum(
            result.status == RequestStatus.SUCCESS for result in self.results
        )
        actual_failures = len(self.results) - actual_successes
        if self.metrics.total_requests != len(self.results):
            raise ValueError("total_requests must match the number of results.")
        if self.metrics.successful_requests != actual_successes:
            raise ValueError("successful_requests does not match result statuses.")
        if self.metrics.failed_requests != actual_failures:
            raise ValueError("failed_requests does not match result statuses.")
        return self
