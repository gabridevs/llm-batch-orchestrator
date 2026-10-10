"""Tests for batch-level Pydantic validation."""

import unittest

from pydantic import ValidationError

from llm_orchestrator.models.requests import BatchRequest, LlmRequest, RequestOperation


def make_request(request_id: str) -> LlmRequest:
    """Create a valid request for model tests."""
    return LlmRequest(
        request_id=request_id,
        provider_name="fast-provider",
        operation=RequestOperation.CLASSIFY,
        prompt="Classify this customer support document accurately.",
    )


class BatchRequestTests(unittest.TestCase):
    """Test validation rules that protect request/result correspondence."""

    def test_rejects_duplicate_request_ids(self) -> None:
        """Duplicate IDs should fail before concurrent work starts."""
        with self.assertRaises(ValidationError):
            BatchRequest(
                requests=(make_request("request-100"), make_request("request-100"))
            )
