"""Slow simulated provider with periodic timeout failures."""

import asyncio

from llm_orchestrator.errors import ProviderTimeoutError
from llm_orchestrator.functional import estimate_tokens
from llm_orchestrator.models.requests import LlmRequest
from llm_orchestrator.models.results import ProviderResponse
from llm_orchestrator.providers.base import BaseProvider


class SlowProvider(BaseProvider):
    """Simulate variable latency and predictable timeout failures."""

    provider_name = "slow-provider"

    def __init__(
        self,
        minimum_latency: float = 0.05,
        maximum_latency: float = 0.15,
        timeout_every: int = 3,
    ) -> None:
        """Configure latency and timeout frequency."""
        self.minimum_latency = minimum_latency
        self.maximum_latency = maximum_latency
        self.timeout_every = timeout_every
        self.call_count = 0

    async def execute(self, request: LlmRequest) -> ProviderResponse:
        """Return a response or raise a periodic timeout."""
        self.call_count += 1
        latency = (
            self.maximum_latency if self.call_count % 2 == 0 else self.minimum_latency
        )
        await asyncio.sleep(latency)
        if self.timeout_every and self.call_count % self.timeout_every == 0:
            raise ProviderTimeoutError("Simulated timeout from slow-provider.")
        return ProviderResponse(
            content=f"{request.operation.value} completed by {self.provider_name}",
            estimated_tokens=estimate_tokens(request.prompt),
        )
