"""Run the packaged benchmark from the repository root."""

import argparse
import asyncio
import json
import sys

from llm_orchestrator.benchmark import run_benchmark


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line arguments for a repeatable benchmark run."""
    parser = argparse.ArgumentParser(description="Benchmark batch strategies.")
    parser.add_argument("--requests", type=int, default=30)
    parser.add_argument("--latency", type=float, default=0.02)
    return parser


async def main(requests: int, latency: float) -> None:
    """Execute the comparison and write rows as JSON to standard output."""
    rows = await run_benchmark(requests, latency)
    sys.stdout.write(json.dumps([row.to_dict() for row in rows], indent=2) + "\n")


if __name__ == "__main__":
    arguments = create_argument_parser().parse_args()
    asyncio.run(main(arguments.requests, arguments.latency))
