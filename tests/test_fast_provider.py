"""Tests for the fast simulated provider."""

import unittest

from llm_orchestrator.models.requests import (
    LlmRequest,
    RequestOperation,
)
from llm_orchestrator.providers.base import BaseProvider
from llm_orchestrator.providers.fast import FastProvider


class FastProviderTests(unittest.IsolatedAsyncioTestCase):
    """Test behavior of FastProvider."""

    def test_provider_is_registered_automatically(self) -> None:
        """Importing the provider should register its class."""
        provider_class = BaseProvider.get_provider_class("fast-provider")

        self.assertIs(provider_class, FastProvider)

    async def test_execute_returns_a_response(self) -> None:
        """The simulated provider should return valid content."""
        provider = FastProvider(latency_seconds=0)

        request = LlmRequest(
            request_id="request-100",
            provider_name="fast-provider",
            operation=RequestOperation.SUMMARIZE,
            prompt="Summarize this technical document clearly.",
        )

        response = await provider.execute(request)

        self.assertIn("summarize", response.content)
        self.assertGreater(response.estimated_tokens, 0)


if __name__ == "__main__":
    unittest.main()
