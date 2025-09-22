# Integration Tests: HTTPX Performance Features

## Background

Hurl relies on httpx for requests to Hilltop servers. httpx provides several features that can dramatically impact request performance, especially for repeated calls to the same server. These features include connection pooling, persistent connections (keep-alive), HTTP/2, and async concurrency.

## Goals

- Identify httpx features that can enhance performance in Hurl (keep-alive, connection reuse, HTTP/2, concurrency, etc.)
- For each feature, design integration tests that clearly demonstrate its performance impact
- Use TDD: write tests *before* implementation changes

## Test Environment Strategies

We support three distinct strategies for running integration and performance tests:

### 1. Remote Server (Internet-Accessible)
- Tests run against a real, internet-accessible API server.
- Used for live integration and for populating/updating the fixture cache with genuine responses.
- **Security:** Remote server config is managed via `.env` file (never committed). `.env` must support both a test and a production server URL.
- **CI:** Remote server tests must never run in CI or any environment with restricted network access.

### 2. Local Server (FastAPI, Real Server on Localhost)
- Tests run against a real server hosted on localhost.
- Implemented with FastAPI for extensibility and simplicity.
- Must serve fixture data from the cache, allow configuration of artificial delays and errors (with sensible, non-random defaults), and bind to 127.0.0.1 by default.
- Fixture mapping can be hardcoded initially, with a view towards config-based mapping later.
- Not a full API simulation, just enough to cover httpx feature scenarios.

### 3. Mocked Server (Fixture Cache)
- No real server; responses are intercepted and served instantly from the fixture cache.
- Strictly for correctness, schema validation, and CI without any network dependency.
- Not suitable for measuring network latency, connection management, or true performance.

### Implementation Notes

- Performance and connection tests **must** target real servers (remote or local). Mocked/cached mode is for correctness tests only.
- Only allow fixture updates using remote servers.
- All test configuration (server URLs, latency simulation, etc.) should be controlled via `.env` file and/or CLI flags. Defaults should be sensible.
- Performance/integration tests are never run by default; they require explicit CLI flags (`--performance-local`, `--performance-remote`).
- Use pytest markers to organize/select tests, but CLI options are the user-facing interface.
- All server-dependent and protocol-dependent tests must be skipped with a clear reason if the required server type or feature is unavailable.

## Action Items

- [ ] Implement a FastAPI-based local test server with configurable fixture serving, delays, and error simulation (hardcoded mapping at first).
- [ ] Implement CLI options: `--performance-local`, `--performance-remote` for explicit test selection.
- [ ] Write integration tests for: sequential requests with/without keep-alive, pooled vs. non-pooled hosts, HTTP/1.1 vs. HTTP/2 concurrency, sync vs. async client concurrency, timeout and retry configuration effects.
- [ ] Ensure all performance/integration tests are opt-in and never run by default.
- [ ] Implement robust skipping logic for unavailable servers/features.
- [ ] Document CLI options, server configuration, and fixture mapping in README.

## CI/CD and Test Selection

- Only run mocked and local server tests in CI (never remote).
- Performance tests may run in CI if they are fast enough; slow ones must be marked (e.g., `@pytest.mark.slow`) and skipped in CI. Not all tests need to be CI-eligible.
- Maintain flexibility to adapt as CI requirements evolve.

## Metrics, Logging, and Reporting

- Use `pytest-benchmark` for timing, concurrency, and throughput metrics. Output should integrate with pytest CLI and respect verbosity flags.
- Connection reuse and protocol metrics can be reported as summary tables in CLI output.
- Do not store logs or historical results in the repo. CI will retain job logs for inspection. Historical comparisons are optional and local for now.

## Configurability

- All remote/test server URLs, and any latency simulation options, must be specified via `.env` (not committed).
- Allow separate test and prod endpoints.
- Delay/error simulation must be configurable and deterministic, not random.

## Test Data and Scenarios

- Start with core endpoints and payload sizes relevant to httpx features.
- Add more scenarios (payload size, concurrency, “stress” cases) as needed.
- Keep initial mapping simple; refactor to config file mapping if tests expand.

---

**Sample pytest-benchmark test:**

```python
import httpx

def test_fastapi_get_latency(benchmark):
    url = "http://localhost:8000/test-endpoint"
    client = httpx.Client()
    result = benchmark(lambda: client.get(url))
    assert result.status_code == 200
```

---

**References:**
- [httpx docs: Performance](https://www.python-httpx.org/performance/)
- [pytest-benchmark docs](https://pytest-benchmark.readthedocs.io/en/latest/)

Let's use this issue to discuss approaches and then start drafting TDD-style integration tests. Suggestions welcome!
