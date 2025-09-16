# Performance Testing for HURL

This document describes the performance testing infrastructure implemented for HURL to test httpx performance features.

## Overview

HURL now includes comprehensive performance tests that demonstrate and validate the performance impact of various httpx features including:

- Connection keep-alive vs new connections
- Connection pooling configurations  
- HTTP/1.1 vs HTTP/2 protocol performance
- Sync vs async client performance
- Concurrency scaling behavior
- Timeout and retry configuration effects

## Test Environment Strategies

### 1. Local Test Server (FastAPI)
- **Purpose**: Performance testing with controlled, local environment
- **Implementation**: FastAPI-based server serving mock Hilltop XML responses
- **Configuration**: Configurable delays, error simulation, and fixture serving
- **Usage**: Enabled with `--performance-local` flag

### 2. Remote Server Testing
- **Purpose**: Real-world performance validation against internet-accessible APIs
- **Configuration**: Via environment variables for security
- **Usage**: Enabled with `--performance-remote` flag (not yet implemented)

### 3. Mocked Responses (Existing)
- **Purpose**: Correctness validation without network dependency
- **Implementation**: Existing pytest-httpx fixture cache system
- **Usage**: Default behavior for CI/CD

## Running Performance Tests

### Prerequisites

Install performance testing dependencies:
```bash
pip install pytest-benchmark fastapi uvicorn
```

### Local Performance Tests

Run performance tests against local FastAPI test server:

```bash
# Run all local performance tests
python -m pytest tests/performance/ --performance-local

# Run specific test categories
python -m pytest tests/performance/test_connection_features.py --performance-local
python -m pytest tests/performance/test_concurrency_features.py --performance-local

# Run with verbose output
python -m pytest tests/performance/ --performance-local -v -s
```

### Configuration

Performance tests can be configured via environment variables:

```bash
# Local test server configuration
export TEST_SERVER_PORT=8001          # Server port (default: 8001)
export TEST_SERVER_DELAY=0.01         # Artificial delay in seconds (default: 0.01)
export TEST_SERVER_ERROR_RATE=0.0     # Error simulation rate 0.0-1.0 (default: 0.0)

# Remote testing configuration (for future implementation)
export HILLTOP_PERFORMANCE_BASE_URL=https://your-test-server.com
export HILLTOP_PERFORMANCE_HTS_ENDPOINT=test.hts
```

## Test Categories

### Connection Management Tests
- **File**: `tests/performance/test_connection_features.py`
- **Features**: Keep-alive connections, connection pooling, pool limits
- **Example Results**:
  ```
  Keep-alive time: 0.1176s
  New connection time: 0.1233s
  Performance improvement: 4.6%
  ```

### Protocol Performance Tests  
- **File**: `tests/performance/test_protocol_features.py`
- **Features**: HTTP/1.1 vs HTTP/2, protocol negotiation
- **Metrics**: Request latency, throughput, protocol version validation

### Concurrency Tests
- **File**: `tests/performance/test_concurrency_features.py`  
- **Features**: Sync vs async clients, concurrent request handling, scaling
- **Example Results**:
  ```
  Concurrency 1: 64.87 RPS
  Concurrency 2: 140.36 RPS  
  Concurrency 5: 268.32 RPS
  Concurrency 10: 398.80 RPS
  ```

### Timeout and Retry Tests
- **File**: `tests/performance/test_timeout_retry.py`
- **Features**: Timeout configurations, retry behavior, error handling
- **Metrics**: Error handling overhead, retry performance impact

## Benchmark Output

Performance tests use `pytest-benchmark` to provide detailed metrics:

```
Name (time in ms)                                Min      Max     Mean  StdDev   Median     IQR  Outliers      OPS  Rounds  Iterations
--------------------------------------------------------------------------------------------------------------------------------------
test_sequential_requests_with_keep_alive     57.1432  58.3662  57.6593  0.2948  57.6226  0.2820       6;1  17.3433      17           1
```

## Design Principles

### Opt-in Testing
- Performance tests **never run by default**
- Require explicit CLI flags (`--performance-local`, `--performance-remote`)
- Skipped with clear messages when flags not provided

### CI/CD Integration
- Only mocked tests run in CI (no network dependencies)
- Performance tests can be added to CI if fast enough
- Slow tests marked with `@pytest.mark.slow` for selective exclusion

### Configurability
- All server URLs, delays, and error rates configurable via environment variables
- Deterministic behavior (no random values)
- Sensible defaults for local development

### TDD Approach
- Tests designed before implementation changes
- Focus on demonstrating clear performance impact
- Quantitative metrics over qualitative assessments

## Local Test Server Details

The FastAPI-based local test server:

- **Endpoint**: `http://127.0.0.1:8001/foo.hts`
- **Health Check**: `http://127.0.0.1:8001/health`
- **XML Format**: Proper HilltopServer format compatible with response parsers
- **Fixture Support**: Serves cached fixture data when available
- **Error Simulation**: Configurable error rates and artificial delays

### Mock Response Example

```xml
<?xml version="1.0" encoding="utf-8"?>
<HilltopServer>
    <Agency>Test</Agency>
    <Version>MockServer-1.0</Version>
    <ScriptName>foo.hts</ScriptName>
    <ProcessID>12345</ProcessID>
    <DataFile>
        <Filename>test.dsn</Filename>
        <UsageCount>1</UsageCount>
    </DataFile>
</HilltopServer>
```

## Future Enhancements

1. **Remote Performance Testing**: Complete implementation of `--performance-remote` flag
2. **HTTP/2 Support**: Enhanced protocol testing when server supports HTTP/2
3. **Historical Benchmarking**: Store and compare performance results over time
4. **Load Testing**: Stress testing scenarios with high concurrency
5. **Configuration-based Fixture Mapping**: Replace hardcoded mapping with config files

## Troubleshooting

### Server Startup Issues
- Check port availability (default 8001)
- Verify FastAPI and uvicorn installation
- Check firewall/security restrictions

### Test Failures
- Ensure performance flags are provided (`--performance-local`)
- Check environment variable configuration
- Verify network connectivity for remote tests

### Slow Performance
- Check `TEST_SERVER_DELAY` configuration
- Verify system resources aren't constrained
- Consider reducing test iteration counts for development