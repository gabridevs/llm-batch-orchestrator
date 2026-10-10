"""Composable decorators for retry, timing, and safe logging."""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from llm_orchestrator.errors import TransientProviderError

Parameters = ParamSpec("Parameters")
Result = TypeVar("Result")
RetryCallback = Callable[[int, TransientProviderError], None]


def retry_async(
    max_attempts: int,
    base_delay_seconds: float,
    on_retry: RetryCallback | None = None,
) -> Callable[
    [Callable[Parameters, Awaitable[Result]]], Callable[Parameters, Awaitable[Result]]
]:
    """Retry an async function only after transient provider failures."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")
    if base_delay_seconds < 0:
        raise ValueError("base_delay_seconds cannot be negative.")

    def decorator(
        function: Callable[Parameters, Awaitable[Result]],
    ) -> Callable[Parameters, Awaitable[Result]]:
        @wraps(function)
        async def wrapper(
            *args: Parameters.args, **kwargs: Parameters.kwargs
        ) -> Result:
            for attempt_number in range(1, max_attempts + 1):
                try:
                    return await function(*args, **kwargs)
                except TransientProviderError as error:
                    if attempt_number == max_attempts:
                        raise
                    if on_retry is not None:
                        on_retry(attempt_number, error)
                    delay_seconds = base_delay_seconds * 2 ** (attempt_number - 1)
                    await asyncio.sleep(delay_seconds)
            raise RuntimeError("Retry loop ended unexpectedly.")

        return wrapper

    return decorator


def timed_async(
    logger: logging.Logger,
) -> Callable[
    [Callable[Parameters, Awaitable[Result]]], Callable[Parameters, Awaitable[Result]]
]:
    """Log safe duration metadata without changing an async result."""

    def decorator(
        function: Callable[Parameters, Awaitable[Result]],
    ) -> Callable[Parameters, Awaitable[Result]]:
        @wraps(function)
        async def wrapper(
            *args: Parameters.args, **kwargs: Parameters.kwargs
        ) -> Result:
            start_time = time.perf_counter()
            try:
                return await function(*args, **kwargs)
            finally:
                logger.debug(
                    "provider_call_timing function=%s elapsed_seconds=%.6f",
                    function.__qualname__,
                    time.perf_counter() - start_time,
                )

        return wrapper

    return decorator


def logged_async(
    logger: logging.Logger,
) -> Callable[
    [Callable[Parameters, Awaitable[Result]]], Callable[Parameters, Awaitable[Result]]
]:
    """Log lifecycle data without logging function arguments or prompts."""

    def decorator(
        function: Callable[Parameters, Awaitable[Result]],
    ) -> Callable[Parameters, Awaitable[Result]]:
        @wraps(function)
        async def wrapper(
            *args: Parameters.args, **kwargs: Parameters.kwargs
        ) -> Result:
            logger.debug("provider_call_started function=%s", function.__qualname__)
            try:
                result = await function(*args, **kwargs)
            except Exception:
                logger.exception(
                    "provider_call_failed function=%s", function.__qualname__
                )
                raise
            logger.debug("provider_call_succeeded function=%s", function.__qualname__)
            return result

        return wrapper

    return decorator
