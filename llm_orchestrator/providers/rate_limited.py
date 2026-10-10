"""Simulated provider with a strict rolling-window rate limit."""

import asyncio
from collections import deque

from llm_orchestrator.errors import RateLimitError
from llm_orchestrator.functional import estimate_tokens
from llm_orchestrator.models.requests import LlmRequest
from llm_orchestrator.models.results import ProviderResponse
from llm_orchestrator.providers.base import BaseProvider


class RateLimitedProvider(BaseProvider):
    """Reject excess requests inside a rolling time window."""

    provider_name = "rate-limited-provider"

    def __init__(
        self,
        max_requests_per_window: int = 2,
        window_seconds: float = 0.1,
        latency_seconds: float = 0.01,
    ) -> None:
        """Configure simulated rate limiting behavior."""
        self.max_requests_per_window = max_requests_per_window
        self.window_seconds = window_seconds
        self.latency_seconds = latency_seconds
        self.request_times: deque[float] = deque()
        self.lock = asyncio.Lock()

    async def execute(self, request: LlmRequest) -> ProviderResponse:
        """Process a request or raise a temporary rate-limit error."""
        async with self.lock:
            current_time = asyncio.get_running_loop().time()
            while (
                self.request_times
                and current_time - self.request_times[0] >= self.window_seconds
            ):
                self.request_times.popleft()
            if len(self.request_times) >= self.max_requests_per_window:
                raise RateLimitError("Rate limit reached for rate-limited-provider.")
            self.request_times.append(current_time)
        await asyncio.sleep(self.latency_seconds)
        return ProviderResponse(
            content=f"{request.operation.value} completed by {self.provider_name}",
            estimated_tokens=estimate_tokens(request.prompt),
        )
