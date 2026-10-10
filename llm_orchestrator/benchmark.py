"""Fair benchmark helpers for sequential and concurrent strategies."""

from dataclasses import asdict, dataclass

from llm_orchestrator.demo import build_demo_batch
from llm_orchestrator.models.config import OrchestratorConfig, RetryConfig
from llm_orchestrator.orchestrator import BatchOrchestrator
from llm_orchestrator.providers.fast import FastProvider
from llm_orchestrator.strategies import (
    AsyncioStrategy,
    SequentialStrategy,
    ThreadingStrategy,
)


@dataclass(frozen=True)
class BenchmarkRow:
    """Store one comparable strategy and concurrency measurement."""

    strategy: str
    max_concurrency: int
    elapsed_seconds: float
    successful_requests: int
    failed_requests: int

    def to_dict(self) -> dict[str, int | float | str]:
        """Return a JSON-serializable representation."""
        return asdict(self)


async def run_benchmark(
    batch_size: int = 30,
    latency_seconds: float = 0.02,
    concurrency_levels: tuple[int, ...] = (1, 3, 6),
) -> tuple[BenchmarkRow, ...]:
    """Compare the same workload across sequential, asyncio, and threading."""
    batch = build_demo_batch(batch_size, "fast-provider")
    rows: list[BenchmarkRow] = []
    comparisons = [(SequentialStrategy(), 1)]
    comparisons.extend(
        (strategy, concurrency)
        for strategy in (AsyncioStrategy(), ThreadingStrategy())
        for concurrency in concurrency_levels
    )

    for strategy, concurrency in comparisons:
        config = OrchestratorConfig(
            max_concurrency=concurrency,
            retry=RetryConfig(max_attempts=1, base_delay_seconds=0),
        )
        orchestrator = BatchOrchestrator(
            config=config,
            providers={"fast-provider": FastProvider(latency_seconds)},
        )
        report = await orchestrator.run(batch, strategy)
        rows.append(
            BenchmarkRow(
                strategy=report.strategy_name,
                max_concurrency=concurrency,
                elapsed_seconds=report.metrics.total_elapsed_seconds,
                successful_requests=report.metrics.successful_requests,
                failed_requests=report.metrics.failed_requests,
            )
        )
    return tuple(rows)
