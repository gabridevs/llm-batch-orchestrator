"""Tests for orchestration, retries, ordering, and concurrency limits."""

import asyncio
import unittest
from unittest.mock import AsyncMock, Mock

from llm_orchestrator.errors import InvalidRequestError, RateLimitError
from llm_orchestrator.models.config import OrchestratorConfig, RetryConfig
from llm_orchestrator.models.requests import BatchRequest, LlmRequest, RequestOperation
from llm_orchestrator.models.results import ProviderResponse, RequestStatus
from llm_orchestrator.orchestrator import BatchOrchestrator
from llm_orchestrator.providers.base import BaseProvider
from llm_orchestrator.strategies import AsyncioStrategy, SequentialStrategy


def make_request(index: int) -> LlmRequest:
    """Create a compact valid request for orchestration tests."""
    return LlmRequest(
        request_id=f"request-{index:03d}",
        provider_name="fast-provider",
        operation=RequestOperation.SUMMARIZE,
        prompt=f"Summarize the important details of document {index}.",
    )


class OrchestratorTests(unittest.IsolatedAsyncioTestCase):
    """Verify external provider calls through AsyncMock instances."""

    def make_orchestrator(
        self, execute: AsyncMock, concurrency: int = 3
    ) -> BatchOrchestrator:
        """Inject a mocked provider into an orchestrator."""
        provider = Mock(spec=BaseProvider)
        provider.execute = execute
        return BatchOrchestrator(
            config=OrchestratorConfig(
                max_concurrency=concurrency,
                retry=RetryConfig(max_attempts=3, base_delay_seconds=0),
            ),
            providers={"fast-provider": provider},
        )

    async def test_retries_transient_failure_and_preserves_success(self) -> None:
        """Rate-limit failure should retry without losing the request result."""
        execute = AsyncMock(
            side_effect=[
                RateLimitError("temporary limit"),
                ProviderResponse(content="completed", estimated_tokens=8),
            ]
        )
        report = await self.make_orchestrator(execute).run(
            BatchRequest(requests=(make_request(1),)),
            SequentialStrategy(),
        )
        result = report.results[0]
        self.assertEqual(execute.await_count, 2)
        self.assertEqual(result.status, RequestStatus.SUCCESS)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(report.metrics.total_retries, 1)
        self.assertEqual(report.successful_results, (result,))
        self.assertEqual(report.failed_results, ())

    async def test_does_not_retry_permanent_failure(self) -> None:
        """Permanent provider failures should be returned immediately."""
        execute = AsyncMock(side_effect=InvalidRequestError("bad request"))
        report = await self.make_orchestrator(execute).run(
            BatchRequest(requests=(make_request(2),)),
            SequentialStrategy(),
        )
        result = report.results[0]
        self.assertEqual(execute.await_count, 1)
        self.assertEqual(result.status, RequestStatus.FAILURE)
        self.assertEqual(result.error_type, "InvalidRequestError")
        self.assertEqual(report.successful_results, ())
        self.assertEqual(report.failed_results, (result,))

    async def test_asyncio_respects_limit_and_restores_input_order(self) -> None:
        """Completion order may differ while result order stays deterministic."""
        active_calls = 0
        maximum_active_calls = 0

        async def delayed_response(request: LlmRequest) -> ProviderResponse:
            nonlocal active_calls, maximum_active_calls
            active_calls += 1
            maximum_active_calls = max(maximum_active_calls, active_calls)
            delay = 0.03 if request.request_id.endswith("000") else 0.005
            await asyncio.sleep(delay)
            active_calls -= 1
            return ProviderResponse(
                content=f"done {request.request_id}",
                estimated_tokens=5,
            )

        execute = AsyncMock(side_effect=delayed_response)
        batch = BatchRequest(requests=tuple(make_request(index) for index in range(5)))
        report = await self.make_orchestrator(execute, concurrency=2).run(
            batch,
            AsyncioStrategy(),
        )
        self.assertLessEqual(maximum_active_calls, 2)
        self.assertEqual(
            [result.request_id for result in report.results],
            [request.request_id for request in batch.requests],
        )
