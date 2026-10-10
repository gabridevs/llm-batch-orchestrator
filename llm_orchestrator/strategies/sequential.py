"""Sequential baseline strategy used for correctness and benchmark comparison."""

from llm_orchestrator.models.requests import LlmRequest
from llm_orchestrator.models.results import RequestResult
from llm_orchestrator.strategies.base import ExecuteRequest


class SequentialStrategy:
    """Execute each request only after the previous one completes."""

    name = "sequential"

    async def execute(
        self,
        requests: tuple[LlmRequest, ...],
        execute_request: ExecuteRequest,
        max_concurrency: int,
    ) -> tuple[RequestResult, ...]:
        """Return sequentially completed results in input order."""
        del max_concurrency
        return tuple([await execute_request(request) for request in requests])
