"""Primary asyncio strategy with semaphore-based concurrency control."""

import asyncio

from llm_orchestrator.models.requests import LlmRequest
from llm_orchestrator.models.results import RequestResult
from llm_orchestrator.strategies.base import ExecuteRequest


class AsyncioStrategy:
    """Execute I/O-bound provider calls concurrently with a semaphore."""

    name = "asyncio"

    async def execute(
        self,
        requests: tuple[LlmRequest, ...],
        execute_request: ExecuteRequest,
        max_concurrency: int,
    ) -> tuple[RequestResult, ...]:
        """Collect completed tasks while returning results in input order."""
        semaphore = asyncio.Semaphore(max_concurrency)
        ordered_results: list[RequestResult | None] = [None] * len(requests)

        async def bounded_execute(
            index: int,
            request: LlmRequest,
        ) -> tuple[int, RequestResult]:
            async with semaphore:
                return index, await execute_request(request)

        tasks = [
            asyncio.create_task(bounded_execute(index, request))
            for index, request in enumerate(requests)
        ]
        try:
            for completed_task in asyncio.as_completed(tasks):
                index, result = await completed_task
                ordered_results[index] = result
        except asyncio.CancelledError:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

        return tuple(result for result in ordered_results if result is not None)
