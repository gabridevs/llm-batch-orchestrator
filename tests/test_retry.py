"""Tests for asynchronous retry behavior."""

import unittest
from unittest.mock import AsyncMock

from llm_orchestrator.decorators import retry_async
from llm_orchestrator.errors import (
    InvalidRequestError,
    RateLimitError,
)


class RetryDecoratorTests(unittest.IsolatedAsyncioTestCase):
    """Test retry decisions for asynchronous operations."""

    async def test_retries_transient_error_then_succeeds(self) -> None:
        """A rate limit should be retried before returning success."""
        operation = AsyncMock(
            side_effect=[
                RateLimitError("Try again later."),
                "completed",
            ]
        )

        decorated_operation = retry_async(
            max_attempts=3,
            base_delay_seconds=0,
        )(operation)

        result = await decorated_operation()

        self.assertEqual(result, "completed")
        self.assertEqual(operation.await_count, 2)

    async def test_does_not_retry_permanent_error(self) -> None:
        """An invalid request should fail immediately."""
        operation = AsyncMock(
            side_effect=InvalidRequestError("Invalid request."),
        )

        decorated_operation = retry_async(
            max_attempts=3,
            base_delay_seconds=0,
        )(operation)

        with self.assertRaises(InvalidRequestError):
            await decorated_operation()

        self.assertEqual(operation.await_count, 1)


if __name__ == "__main__":
    unittest.main()
