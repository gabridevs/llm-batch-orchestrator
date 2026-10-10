# LLM Batch Orchestrator

Installable Python library for resilient batch execution against simulated LLM
providers. It is designed for I/O-bound provider calls: it preserves the link
between every request and result, limits concurrency, retries transient
failures, and returns partial successes when other requests fail.

Run the interactive [Google Colab demo](https://colab.research.google.com/github/gabridevs/llm-batch-orchestrator/blob/main/notebooks/llm_batch_orchestrator_demo.ipynb).

## Features

- Pydantic v2 models validate immutable requests, batches, results, metrics,
  retry configuration, and result/report consistency.
- Automatic provider registry using `BaseProvider.__init_subclass__`.
- Three simulated providers: reliable/fast, variable/timeout-prone, and
  rolling-window rate-limited.
- Interchangeable sequential, `asyncio`, and threading strategies.
- `asyncio.Semaphore` enforces the configured concurrent-call ceiling.
- Exponential retry/backoff only for transient provider errors.
- Structured per-request success/failure records; no completed work is lost.
- Metrics for elapsed time, success/failure counts, retries, and estimated
  token use.
- Hierarchical logging with console and rotating-file handlers. Prompts and
  secrets are never written to logs.

## Install with Poetry

```bash
poetry install
poetry run llm-batch-orchestrator run --requests 12 --strategy asyncio
```

The command writes a JSON report to `output/report.json`. Try other providers:

```bash
poetry run llm-batch-orchestrator run --provider slow-provider
poetry run llm-batch-orchestrator run --provider rate-limited-provider
```

## CLI

```bash
# Build a report with a chosen strategy and limit
poetry run llm-batch-orchestrator run \
  --strategy asyncio --concurrency 3 --requests 20

# Compare sequential, asyncio, and threading
poetry run llm-batch-orchestrator benchmark --requests 30 --latency 0.02
```

## Architecture

```text
BatchRequest (Pydantic validation)
    -> BatchOrchestrator.execute_one
    -> execution strategy
       -> provider.execute
    -> RequestResult for every input request
    -> BatchReport + ExecutionMetrics
```

`AsyncioStrategy` creates one task per request, but wraps the actual provider
call in `asyncio.Semaphore(max_concurrency)`. Results are collected as tasks
finish and written into their original indexes, so completion order never
changes request/result correspondence.

## Why asyncio is the primary strategy

LLM API calls spend most of their time waiting for network I/O. During
`await`, asyncio can run another request in the same thread with low overhead.
The GIL matters for CPU-bound Python code, but it does not prevent useful
concurrency while waiting for I/O. Threading is included as a comparison
strategy; it can help with blocking libraries, but adds thread and context
switching overhead.

Multiprocessing is intentionally not used: it duplicates process memory and
has expensive serialization/IPC costs while the bottleneck is waiting on a
provider, not CPU computation. It would be appropriate for genuinely
CPU-heavy local post-processing instead.

## Error policy

```text
RateLimitError / ProviderTimeoutError -> retry with exponential backoff
InvalidRequestError / ProviderNotFoundError -> fail immediately
```

Each failure becomes a `RequestResult` with `error_type` and `error_message`.
The rest of the batch keeps running.

## TDD and tests

The early model work followed a red-green loop: tests for blank prompts and
invalid provider names were written before their validators. Retry tests were
also written before `retry_async` existed. The suite uses `unittest` and
`AsyncMock` for every provider call in orchestration tests.

```bash
poetry run python -m unittest discover -s tests
poetry run ruff check .
```

Covered behavior includes success, transient retry, permanent no-retry,
semaphore concurrency limits, out-of-order completion with ordered results,
automatic registration, and batch ID validation.

## Benchmark

See [benchmarks/README.md](benchmarks/README.md). The benchmark uses the same
input batch and measures sequential, asyncio, and threading at limits 1, 3,
and 6. Expect diminishing returns once additional in-flight calls no longer
hide meaningful provider latency.
