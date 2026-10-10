"""Thread-pool comparison strategy for the same asynchronous provider interface."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from llm_orchestrator.models.requests import LlmRequest
from llm_orchestrator.models.results import RequestResult
from llm_orchestrator.strategies.base import ExecuteRequest


class ThreadingStrategy:
    """Run isolated event loops in worker threads for comparison purposes."""

    name = "threading"

    async def execute(
        self,
        requests: tuple[LlmRequest, ...],
        execute_request: ExecuteRequest,
        max_concurrency: int,
    ) -> tuple[RequestResult, ...]:
        """Execute requests in threads and restore original result order."""
        loop = asyncio.get_running_loop()
        ordered_results: list[RequestResult | None] = [None] * len(requests)

        def run_request(index: int, request: LlmRequest) -> tuple[int, RequestResult]:
            return index, asyncio.run(execute_request(request))

        with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
            tasks = [
                loop.run_in_executor(executor, run_request, index, request)
                for index, request in enumerate(requests)
            ]
            for completed_task in asyncio.as_completed(tasks):
                index, result = await completed_task
                ordered_results[index] = result

        return tuple(result for result in ordered_results if result is not None)
