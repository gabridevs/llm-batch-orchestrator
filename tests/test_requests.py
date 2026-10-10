"""Tests for input request models."""

import unittest

from pydantic import ValidationError

from llm_orchestrator.models.requests import (
    LlmRequest,
    RequestOperation,
)


class LlmRequestTests(unittest.TestCase):
    """Test validation behavior of LlmRequest."""

    def test_creates_valid_request(self) -> None:
        """A complete request should be created successfully."""
        request = LlmRequest(
            request_id="request-001",
            provider_name="fast-provider",
            operation=RequestOperation.SUMMARIZE,
            prompt="Summarize this document.",
        )

        self.assertEqual(request.request_id, "request-001")
        self.assertEqual(
            request.operation,
            RequestOperation.SUMMARIZE,
        )

    def test_rejects_blank_prompt(self) -> None:
        """A prompt containing only spaces should be rejected."""
        with self.assertRaises(ValidationError):
            LlmRequest(
                request_id="request-002",
                provider_name="fast-provider",
                operation=RequestOperation.CLASSIFY,
                prompt="   ",
            )

    def test_rejects_invalid_provider_name(self) -> None:
        """Provider names should use lowercase letters, digits, and hyphens."""
        with self.assertRaises(ValidationError):
            LlmRequest(
                request_id="request-003",
                provider_name="Fast Provider!",
                operation=RequestOperation.EXTRACT,
                prompt="Extract the required customer fields.",
            )


if __name__ == "__main__":
    unittest.main()
