"""Command-line interface for demo runs and strategy benchmarks."""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from llm_orchestrator.benchmark import run_benchmark
from llm_orchestrator.demo import build_demo_batch
from llm_orchestrator.logging_config import configure_logging
from llm_orchestrator.models.config import OrchestratorConfig
from llm_orchestrator.orchestrator import BatchOrchestrator
from llm_orchestrator.strategies import (
    AsyncioStrategy,
    SequentialStrategy,
    ThreadingStrategy,
)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line parser and its subcommands."""
    parser = argparse.ArgumentParser(description="Run the LLM batch orchestrator demo.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a simulated batch.")
    run_parser.add_argument(
        "--strategy", choices=("sequential", "asyncio", "threading"), default="asyncio"
    )
    run_parser.add_argument(
        "--provider",
        choices=("fast-provider", "slow-provider", "rate-limited-provider"),
        default="fast-provider",
    )
    run_parser.add_argument("--requests", type=int, default=12)
    run_parser.add_argument("--concurrency", type=int, default=3)
    run_parser.add_argument("--output", type=Path, default=Path("output/report.json"))

    benchmark_parser = subparsers.add_parser("benchmark", help="Compare strategies.")
    benchmark_parser.add_argument("--requests", type=int, default=30)
    benchmark_parser.add_argument("--latency", type=float, default=0.02)
    benchmark_parser.add_argument(
        "--output", type=Path, default=Path("output/benchmark.json")
    )
    return parser


def strategy_from_name(
    name: str,
) -> SequentialStrategy | AsyncioStrategy | ThreadingStrategy:
    """Create one strategy object from a CLI choice."""
    strategies = {
        "sequential": SequentialStrategy,
        "asyncio": AsyncioStrategy,
        "threading": ThreadingStrategy,
    }
    return strategies[name]()


def write_json(output_path: Path, data: object) -> None:
    """Write JSON output while creating its parent directory when needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


async def run_command(arguments: argparse.Namespace) -> dict[str, object]:
    """Run one demo batch and return a serializable report."""
    batch = build_demo_batch(arguments.requests, arguments.provider)
    config = OrchestratorConfig(max_concurrency=arguments.concurrency)
    report = await BatchOrchestrator(config).run(
        batch,
        strategy_from_name(arguments.strategy),
    )
    return report.model_dump(mode="json")


def main() -> None:
    """Execute the command-line application."""
    parser = create_argument_parser()
    arguments = parser.parse_args()
    if arguments.command == "run":
        configure_logging(level=logging.INFO)
        data = asyncio.run(run_command(arguments))
    else:
        configure_logging(level=logging.WARNING)
        rows = asyncio.run(run_benchmark(arguments.requests, arguments.latency))
        data = {"rows": [row.to_dict() for row in rows]}
    write_json(arguments.output, data)
    sys.stdout.write(f"Saved output to {arguments.output}\n")


if __name__ == "__main__":
    main()
