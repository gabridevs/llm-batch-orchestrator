"""Common protocol for interchangeable execution strategies."""

from collections.abc import Awaitable, Callable
from typing import Protocol

from llm_orchestrator.models.requests import LlmRequest
from llm_orchestrator.models.results import RequestResult

ExecuteRequest = Callable[[LlmRequest], Awaitable[RequestResult]]


class ExecutionStrategy(Protocol):
    """Execute a batch while preserving request-to-result correspondence."""

    name: str

    async def execute(
        self,
        requests: tuple[LlmRequest, ...],
        execute_request: ExecuteRequest,
        max_concurrency: int,
    ) -> tuple[RequestResult, ...]:
        """Return results in the same order as input requests."""
