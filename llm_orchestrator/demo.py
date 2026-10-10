"""Deterministic demo batches shared by the CLI, notebook, and benchmarks."""

from llm_orchestrator.models.requests import BatchRequest, LlmRequest, RequestOperation


def build_demo_batch(size: int, provider_name: str) -> BatchRequest:
    """Build a reproducible batch with valid prompts and unique request IDs."""
    if size < 1:
        raise ValueError("size must be at least 1.")
    operations = tuple(RequestOperation)
    requests = tuple(
        LlmRequest(
            request_id=f"request-{index:04d}",
            provider_name=provider_name,
            operation=operations[index % len(operations)],
            prompt=(
                "Process document number "
                f"{index} using the requested simulated LLM operation."
            ),
        )
        for index in range(size)
    )
    return BatchRequest(requests=requests)
