"""Fast and reliable simulated provider."""

import asyncio

from llm_orchestrator.functional import estimate_tokens
from llm_orchestrator.models.requests import LlmRequest
from llm_orchestrator.models.results import ProviderResponse
from llm_orchestrator.providers.base import BaseProvider


class FastProvider(BaseProvider):
    """Simulate a fast provider that always succeeds."""

    provider_name = "fast-provider"

    def __init__(self, latency_seconds: float = 0.01) -> None:
        """Configure simulated network latency."""
        self.latency_seconds = latency_seconds

    async def execute(self, request: LlmRequest) -> ProviderResponse:
        """Return a deterministic successful response."""
        await asyncio.sleep(self.latency_seconds)
        return ProviderResponse(
            content=f"{request.operation.value} completed by {self.provider_name}",
            estimated_tokens=estimate_tokens(request.prompt),
        )
