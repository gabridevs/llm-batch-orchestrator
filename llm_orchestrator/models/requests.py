"""Validated input models for batch orchestration."""

import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RequestOperation(StrEnum):
    """Describe the LLM operations supported by the demo providers."""

    CLASSIFY = "classify"
    SUMMARIZE = "summarize"
    EXTRACT = "extract"


class LlmRequest(BaseModel):
    """Represent one immutable, validated request for an LLM provider."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    request_id: str = Field(description="Identifier that links input and result.")
    provider_name: str = Field(description="Canonical provider name.")
    operation: RequestOperation
    prompt: str = Field(description="Text sent to the provider.")

    @field_validator("request_id")
    @classmethod
    def validate_request_id(cls, value: str) -> str:
        """Require stable identifiers safe for logs and result matching."""
        if not re.fullmatch(r"[a-z][a-z0-9_-]{2,63}", value):
            raise ValueError(
                "request_id must use 3-64 lowercase letters, digits, "
                "underscores, or hyphens."
            )
        return value

    @field_validator("provider_name")
    @classmethod
    def validate_provider_name(cls, value: str) -> str:
        """Validate the canonical name used to select a provider."""
        valid_name = re.fullmatch(r"[a-z][a-z0-9-]{2,31}", value)
        if not valid_name or "--" in value:
            raise ValueError(
                "provider_name must use 3-32 lowercase letters, "
                "digits, or single hyphens."
            )
        return value

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        """Normalize whitespace and reject empty or impractically large text."""
        normalized_value = " ".join(value.split())
        if not normalized_value:
            raise ValueError("prompt must contain non-whitespace text.")
        if len(normalized_value) < 10:
            raise ValueError("prompt must contain at least 10 characters.")
        if len(normalized_value) > 12_000:
            raise ValueError("prompt cannot exceed 12,000 characters.")
        return normalized_value


class BatchRequest(BaseModel):
    """Represent an immutable validated collection of LLM requests."""

    model_config = ConfigDict(frozen=True)

    requests: tuple[LlmRequest, ...] = Field(min_length=1, max_length=10_000)

    @model_validator(mode="after")
    def validate_unique_request_ids(self) -> "BatchRequest":
        """Reject duplicate IDs that make result matching ambiguous."""
        seen_request_ids: set[str] = set()
        duplicated_request_ids: set[str] = set()
        for request in self.requests:
            if request.request_id in seen_request_ids:
                duplicated_request_ids.add(request.request_id)
            seen_request_ids.add(request.request_id)
        if duplicated_request_ids:
            duplicates = ", ".join(sorted(duplicated_request_ids))
            raise ValueError(
                f"Batch contains duplicated request_id values: {duplicates}."
            )
        return self
