"""Validated configuration models for orchestration."""

from pydantic import BaseModel, ConfigDict, Field


class RetryConfig(BaseModel):
    """Configure retry attempts and exponential backoff."""

    model_config = ConfigDict(frozen=True)

    max_attempts: int = Field(default=3, ge=1, le=10)
    base_delay_seconds: float = Field(default=0.05, ge=0, le=60)


class OrchestratorConfig(BaseModel):
    """Configure concurrency, timeout, and retry behavior."""

    model_config = ConfigDict(frozen=True)

    max_concurrency: int = Field(default=5, ge=1, le=1_000)
    timeout_seconds: float = Field(default=1.0, gt=0, le=300)
    retry: RetryConfig = Field(default_factory=RetryConfig)
