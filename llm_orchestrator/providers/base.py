"""Base interface and automatic registry for LLM providers."""

from abc import ABC, abstractmethod
from typing import ClassVar

from llm_orchestrator.errors import ProviderNotFoundError
from llm_orchestrator.models.requests import LlmRequest
from llm_orchestrator.models.results import ProviderResponse


class BaseProvider(ABC):
    """Define the common asynchronous interface for LLM providers."""

    provider_name: ClassVar[str] = ""
    registry: ClassVar[dict[str, type["BaseProvider"]]] = {}

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Register concrete provider subclasses automatically."""
        super().__init_subclass__(**kwargs)
        if not cls.provider_name:
            return
        if cls.provider_name in BaseProvider.registry:
            raise ValueError(f"Provider '{cls.provider_name}' is already registered.")
        BaseProvider.registry[cls.provider_name] = cls

    @classmethod
    def get_provider_class(cls, provider_name: str) -> type["BaseProvider"]:
        """Return the registered provider class for a canonical name."""
        try:
            return cls.registry[provider_name]
        except KeyError as error:
            raise ProviderNotFoundError(
                f"Provider '{provider_name}' is not registered."
            ) from error

    @abstractmethod
    async def execute(self, request: LlmRequest) -> ProviderResponse:
        """Execute one validated request asynchronously."""
