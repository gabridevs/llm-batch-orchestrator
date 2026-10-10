"""Core batch orchestrator shared by sequential, asyncio, and threading strategies."""

import asyncio
import logging
import time
from collections.abc import Mapping

import llm_orchestrator.providers  # noqa: F401
from llm_orchestrator.decorators import logged_async, retry_async, timed_async
from llm_orchestrator.errors import ProviderError, ProviderTimeoutError
from llm_orchestrator.functional import request_summary
from llm_orchestrator.metrics import build_execution_metrics
from llm_orchestrator.models.config import OrchestratorConfig
from llm_orchestrator.models.reports import BatchReport
from llm_orchestrator.models.requests import BatchRequest, LlmRequest
from llm_orchestrator.models.results import (
    ProviderResponse,
    RequestResult,
    RequestStatus,
)
from llm_orchestrator.providers.base import BaseProvider
from llm_orchestrator.strategies.base import ExecutionStrategy


class BatchOrchestrator:
    """Execute validated request batches without losing partial progress."""

    def __init__(
        self,
        config: OrchestratorConfig | None = None,
        providers: Mapping[str, BaseProvider] | None = None,
    ) -> None:
        """Create an orchestrator with optional injected provider instances."""
        self.config = config or OrchestratorConfig()
        self.providers = dict(providers or {})
        self.logger = logging.getLogger("llm_orchestrator.orchestrator")

    def get_provider(self, provider_name: str) -> BaseProvider:
        """Return a shared provider instance, constructing registered providers lazily."""
        if provider_name not in self.providers:
            provider_class = BaseProvider.get_provider_class(provider_name)
            self.providers[provider_name] = provider_class()
        return self.providers[provider_name]

    async def execute_one(self, request: LlmRequest) -> RequestResult:
        """Execute one request and convert every failure into a structured result."""
        start_time = time.perf_counter()
        retry_count = 0
        safe_request_data = request_summary(request)

        def count_retry(attempt_number: int, error: ProviderError) -> None:
            nonlocal retry_count
            retry_count += 1
            self.logger.warning(
                "request_retry request_id=%s provider=%s retry=%s error=%s",
                safe_request_data["request_id"],
                safe_request_data["provider_name"],
                attempt_number,
                type(error).__name__,
            )

        try:
            provider = self.get_provider(request.provider_name)

            async def call_provider() -> ProviderResponse:
                try:
                    return await asyncio.wait_for(
                        provider.execute(request),
                        timeout=self.config.timeout_seconds,
                    )
                except TimeoutError as error:
                    raise ProviderTimeoutError(
                        f"Provider '{request.provider_name}' timed out."
                    ) from error

            protected_call = retry_async(
                max_attempts=self.config.retry.max_attempts,
                base_delay_seconds=self.config.retry.base_delay_seconds,
                on_retry=count_retry,
            )(timed_async(self.logger)(logged_async(self.logger)(call_provider)))
            response = await protected_call()
            result = RequestResult(
                request_id=request.request_id,
                provider_name=request.provider_name,
                status=RequestStatus.SUCCESS,
                content=response.content,
                attempts=retry_count + 1,
                elapsed_seconds=time.perf_counter() - start_time,
                estimated_tokens=response.estimated_tokens,
            )
            self.logger.info(
                "request_succeeded request_id=%s provider=%s attempts=%s",
                request.request_id,
                request.provider_name,
                result.attempts,
            )
            return result
        except ProviderError as error:
            return self._failure_result(request, retry_count, start_time, error)
        except Exception as error:
            self.logger.exception(
                "request_unexpected_failure request_id=%s provider=%s",
                request.request_id,
                request.provider_name,
            )
            return self._failure_result(request, retry_count, start_time, error)

    def _failure_result(
        self,
        request: LlmRequest,
        retry_count: int,
        start_time: float,
        error: Exception,
    ) -> RequestResult:
        """Create and log one failure result without stopping the batch."""
        self.logger.warning(
            "request_failed request_id=%s provider=%s error=%s",
            request.request_id,
            request.provider_name,
            type(error).__name__,
        )
        return RequestResult(
            request_id=request.request_id,
            provider_name=request.provider_name,
            status=RequestStatus.FAILURE,
            error_type=type(error).__name__,
            error_message=str(error),
            attempts=retry_count + 1,
            elapsed_seconds=time.perf_counter() - start_time,
            estimated_tokens=0,
        )

    async def run(
        self,
        batch: BatchRequest,
        strategy: ExecutionStrategy,
    ) -> BatchReport:
        """Run a batch with a selected strategy and return an ordered report."""
        start_time = time.perf_counter()
        results = await strategy.execute(
            batch.requests,
            self.execute_one,
            self.config.max_concurrency,
        )
        elapsed_seconds = time.perf_counter() - start_time
        metrics = build_execution_metrics(results, elapsed_seconds)
        return BatchReport(
            strategy_name=strategy.name,
            results=results,
            metrics=metrics,
        )
