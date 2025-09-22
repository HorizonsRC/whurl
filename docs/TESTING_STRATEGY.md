# WHURL Testing Strategy

This document outlines the comprehensive testing approach used in WHURL to ensure robust, reliable functionality while supporting both offline development and live API validation.

## Overview

WHURL implements a multi-layered testing strategy that supports:
- **Fast offline development** with unit tests using mocked data
- **Reliable integration testing** using cached API responses
- **Performance validation** for HTTP client optimizations  
- **Live API validation** against real Hilltop servers when needed

## Test Categories

### 1. Unit Tests (`--mode=unit`)
**Purpose**: Fast, isolated testing of individual components without external dependencies.

**Characteristics**:
- Use mocked data from `tests/mocked_data/`
- No network calls or external dependencies
- Fast execution (< 3 seconds total)
- Always reliable in offline environments
- Cover core functionality and edge cases

**Usage**:
```bash
# Poetry (Recommended)
poetry run python -m pytest tests/ --mode=unit

# pip/direct Python
python -m pytest tests/ --mode=unit
```

**When to Use**:
- Daily development and debugging
- CI/CD pipelines 
- Offline development environments
- When you need guaranteed fast, reliable test results

### 2. Integration Tests (`--mode=integration`)
**Purpose**: Test component interactions using realistic data without making live API calls.

**Characteristics**:
- Use cached XML responses from `tests/fixture_cache/`
- Test realistic API response parsing and schema validation
- Depend on fixture files being present in repository
- Validate end-to-end request → response → parsing workflows

**Usage**:
```bash
# Poetry (Recommended)
poetry run python -m pytest tests/ --mode=integration

# pip/direct Python  
python -m pytest tests/ --mode=integration
```

**When to Use**:
- Testing after schema changes
- Validating parsing logic with realistic data
- Before releases to ensure integration scenarios work
- When fixture cache files are available

### 3. Performance Tests (`--mode=performance`)
**Purpose**: Validate HTTP client performance features and optimizations.

**Characteristics**:
- Test connection pooling, keep-alive, HTTP/2, timeouts, retries
- Use local FastAPI test server for controlled testing
- Generate quantitative performance metrics
- Never run by default (opt-in only)

**Usage**:
```bash
# Performance tests require explicit flags
poetry run python -m pytest tests/performance/ --performance-local

# Run specific performance categories
poetry run python -m pytest tests/performance/test_connection_features.py --performance-local
```

**When to Use**:
- Validating HTTP client configuration changes
- Before releases to ensure performance characteristics
- When investigating client performance issues

See [Performance Testing Documentation](PERFORMANCE_TESTING.md) for detailed information.

### 4. Remote Tests (`@pytest.mark.remote`)
**Purpose**: Validate against live Hilltop API endpoints.

**Characteristics**:
- Make actual HTTP calls to configured endpoints
- Can update cached fixture files with `--update` flag
- Require network connectivity and valid API endpoints
- Used to keep cached fixtures current with API changes

**Usage**:
```bash
# Set environment variables for real endpoints
export HILLTOP_BASE_URL="https://your-hilltop-server.com"
export HILLTOP_HTS_ENDPOINT="your-endpoint.hts"

# Update cached fixtures from remote APIs
poetry run python -m pytest --update --mode=integration

# Validate cached responses against remote APIs  
poetry run python -m pytest tests/ -m remote
```

**When to Use**:
- Updating fixture cache with latest API responses
- Validating API changes haven't broken parsing logic
- Ensuring cached data matches current API behavior

## Testing Modes

### Offline Mode (`--mode=offline`) 
**Default behavior** - runs all tests that don't require network connectivity.

**Includes**:
- All unit tests (using mocked data)
- Integration tests (using cached fixtures, may fail if files missing)
- Performance tests are skipped

**Best For**: General development, CI/CD

### Test Organization

```
tests/
├── mocked_data/           # Static XML samples for unit tests
│   ├── collection_list/
│   ├── get_data/
│   ├── measurement_list/
│   ├── site_info/
│   ├── site_list/
│   ├── status/
│   └── time_range/
├── fixture_cache/         # Cached API responses for integration tests
│   ├── collection_list/   # (Same structure as mocked_data)
│   └── ...
├── performance/           # Performance validation tests
│   ├── test_connection_features.py
│   ├── test_concurrency_features.py
│   └── test_protocol_features.py
├── test_schemas/          # Schema validation tests
│   ├── test_requests/
│   └── test_responses/
└── test_utils.py          # Utility function tests
```

## Environment Setup

### Required Environment Variables

For client testing and integration tests:
```bash
export HILLTOP_BASE_URL="https://data.council.govt.nz"
export HILLTOP_HTS_ENDPOINT="foo.hts"
```

**Note**: These example values are for testing only and do not represent a real working API endpoint.

### Optional Environment Variables

For performance testing:
```bash
export TEST_SERVER_PORT=8001          # Local test server port
export TEST_SERVER_DELAY=0.01         # Artificial delay in seconds
export TEST_SERVER_ERROR_RATE=0.0     # Error simulation rate (0.0-1.0)
```

For remote API testing:
```bash
export HILLTOP_PERFORMANCE_BASE_URL=https://your-test-server.com
export HILLTOP_PERFORMANCE_HTS_ENDPOINT=test.hts
```

## Fixture Cache System

### How It Works

1. **Mocked Data**: Static XML files in `tests/mocked_data/` used for unit tests
2. **Cached Fixtures**: Real API responses stored in `tests/fixture_cache/` used for integration tests  
3. **Update Mechanism**: `--update` flag refreshes cached files from live APIs
4. **Selective Mocking**: `httpx_mock` system bypasses mocks for specific domains during updates

### Updating Fixtures

```bash
# Update all cached fixtures (requires network connectivity)
poetry run python -m pytest --update --mode=integration

# Update specific test fixtures
poetry run python -m pytest tests/test_schemas/test_responses/test_site_list_response.py --update --mode=integration
```

### Cache Management

- Cached files are committed to repository for offline development
- Update cache periodically to detect API changes
- If cache files are missing, integration tests will fail with clear error messages

## Common Testing Scenarios

### Daily Development
```bash
# Fast, reliable unit tests only
poetry run python -m pytest tests/ --mode=unit --quiet
```

### Before Code Commits  
```bash
# All offline tests
poetry run python -m pytest tests/ --mode=offline
```

### Before Releases
```bash
# Unit tests
poetry run python -m pytest tests/ --mode=unit

# Integration tests (if fixtures available)
poetry run python -m pytest tests/ --mode=integration

# Performance validation
poetry run python -m pytest tests/performance/ --performance-local
```

### Updating API Fixtures
```bash
# Set real API endpoints
export HILLTOP_BASE_URL="https://real-server.com"
export HILLTOP_HTS_ENDPOINT="real.hts"

# Update cached fixtures
poetry run python -m pytest --update --mode=integration
```

## Troubleshooting

### Tests Fail Due to Missing Fixtures
**Error**: `FileNotFoundError: [Errno 2] No such file or directory: '.../tests/fixture_cache/.../*.xml'`

**Solution**: Run unit tests only, or update fixtures from remote API:
```bash
poetry run python -m pytest tests/ --mode=unit
```

### Performance Tests Don't Run
**Issue**: Performance tests are skipped

**Solution**: Performance tests require explicit flags:
```bash
poetry run python -m pytest tests/performance/ --performance-local
```

### Integration Tests Take Too Long  
**Issue**: Integration tests are slow in CI/CD

**Solution**: Use unit tests for fast feedback:
```bash
poetry run python -m pytest tests/ --mode=unit
```

### Remote Tests Fail
**Issue**: Cannot connect to remote API

**Solutions**:
1. Check network connectivity
2. Verify environment variables are set correctly
3. Use cached fixtures instead:
   ```bash
   poetry run python -m pytest tests/ --mode=integration
   ```

## Design Principles

### Reliability First
- Unit tests must always pass in offline environments
- Integration tests gracefully handle missing fixtures
- Clear error messages when external dependencies unavailable

### Performance Conscious
- Fast feedback loop with unit tests (< 3 seconds)
- Longer integration/performance tests are opt-in
- Cached fixtures avoid repeated API calls

### Maintainability
- Clear separation between test types and data sources
- Fixture cache system reduces maintenance overhead
- Comprehensive documentation for debugging issues

### CI/CD Friendly
- Default offline mode works without network dependencies
- Predictable test execution times
- Clear exit codes and error messages