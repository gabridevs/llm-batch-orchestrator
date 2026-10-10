"""Output models for provider and orchestration results."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RequestStatus(StrEnum):
    """Describe whether a request succeeded or failed."""

    SUCCESS = "success"
    FAILURE = "failure"


class ProviderResponse(BaseModel):
    """Represent a successful normalized response from one provider."""

    model_config = ConfigDict(frozen=True)

    content: str = Field(min_length=1)
    estimated_tokens: int = Field(ge=0)


class RequestResult(BaseModel):
    """Represent final success or failure for one input request."""

    model_config = ConfigDict(frozen=True)

    request_id: str
    provider_name: str
    status: RequestStatus
    content: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    attempts: int = Field(ge=1)
    elapsed_seconds: float = Field(ge=0)
    estimated_tokens: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_result_consistency(self) -> "RequestResult":
        """Ensure success and failure records have coherent fields."""
        if self.status == RequestStatus.SUCCESS and not self.content:
            raise ValueError("Successful results must contain response content.")
        if self.status == RequestStatus.FAILURE and (
            not self.error_type or not self.error_message
        ):
            raise ValueError("Failed results must contain an error type and message.")
        return self
