# Benchmark methodology

`run_benchmark.py` sends the same deterministic batch to `FastProvider` under:

- sequential execution;
- `asyncio` with concurrency limits 1, 3, and 6;
- threading with the same limits.

The simulated provider waits for I/O using `asyncio.sleep`, so the experiment
models network waiting rather than CPU-heavy inference. Run it with:

```bash
poetry run python benchmarks/run_benchmark.py --requests 30 --latency 0.02
```

## Measured run

On this project machine, with 30 requests and 20 ms simulated I/O latency, a
representative run produced the following values (seconds):

| Strategy | Concurrency | Time |
| --- | ---: | ---: |
| sequential | 1 | 0.636 |
| asyncio | 1 | 0.665 |
| asyncio | 3 | 0.212 |
| asyncio | 6 | 0.107 |
| threading | 1 | 0.661 |
| threading | 3 | 0.228 |
| threading | 6 | 0.122 |

`asyncio` wins at the useful concurrent limits. With a limit of 1 it has a
small scheduling cost, so it is not faster than sequential execution. At 3
and 6 the outstanding waits overlap; the improvement is close to the chosen
limit for this deliberately uniform workload. Real providers eventually hit
rate limits, server queues, or bandwidth limits, so raising the limit forever
does not keep improving throughput.

The useful comparison is not an exact duration—hardware changes that—but the
trend. `asyncio` should improve almost linearly until concurrency roughly
matches the number of simultaneous waits. After that, increasing concurrency
has diminishing returns. The threading strategy can complete the same I/O
work, but is expected to add overhead because it creates event loops inside
worker threads. Sequential execution is the baseline and should be slowest.

If a run contradicts this expectation, keep the result: inspect batch size,
simulated latency, machine load, logging level, and provider rate limits
instead of assuming the theoretical result must win.
