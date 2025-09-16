# HURL Developer Testing Guide

This guide covers the advanced test scheme and data sources implemented in HURL for performance and integration testing.

## Test Data Sources

HURL supports three distinct test data sources with automatic fallback:

### 1. 🎭 Mocked Data (Always Available)
- **Location**: `tests/mocked_data/`
- **Purpose**: Anonymized XML fixtures checked into repository
- **Use Case**: CI/CD, unit tests, onboarding
- **Availability**: ✅ Always available (checked into repo)
- **Security**: ✅ Safe (no sensitive data)

### 2. 💾 Cached Data (Local Development)  
- **Location**: `tests/fixture_cache/`
- **Purpose**: Local cache of real remote API responses
- **Use Case**: Fast offline development with realistic data
- **Availability**: ⚠️ Must be generated locally (not in CI)
- **Security**: ⚠️ May contain sensitive data (never committed)

### 3. 🌐 Remote Data (Live API)
- **Location**: Direct API calls to live servers
- **Purpose**: Cache refresh, high-fidelity integration testing
- **Use Case**: Fixture updates, integration validation
- **Availability**: ⚠️ Requires network + credentials
- **Security**: ⚠️ Sensitive (never for CI)

## Test Classification

### 🧪 Unit Tests
```bash
pytest -m unit
```
- Use only mocked data
- Fast and reliable
- Run in CI
- No network dependencies

### 🔧 Integration Tests  
```bash
pytest -m integration
```
- Can use any data source
- Test end-to-end functionality
- May require environment setup

### ⚡ Performance Tests
```bash
pytest -m performance  
```
- Prefer real data when available
- Measure parsing vs network latency
- Detect regressions

## CLI Usage

### Data Source Selection
```bash
# Auto-select (cached → mocked fallback)
pytest --data-source=auto

# Force mocked data only (CI-safe)
pytest --data-source=mocked

# Prefer cached data
pytest --data-source=cached

# Force remote API calls (requires credentials)
pytest --data-source=remote
```

### Test Categories
```bash
# Run only unit tests (fast, CI-safe)
pytest -m unit

# Run integration tests with mocked data
pytest -m integration --data-source=mocked

# Run performance tests with real data
pytest -m performance --data-source=cached

# Skip remote-dependent tests
pytest -m "not remote"
```

### Fixture Management
```bash
# Update cached fixtures from remote API
pytest --update -m "remote and update"

# Skip tests when data unavailable
pytest --skip-missing-data

# Verbose data source reporting
pytest -v --data-source=auto
```

## Environment Setup

### Required Environment Variables
```bash
export HILLTOP_BASE_URL="https://your-hilltop-server.com"
export HILLTOP_HTS_ENDPOINT="your-endpoint.hts"
```

Or create `.env` file:
```env
HILLTOP_BASE_URL=https://your-hilltop-server.com
HILLTOP_HTS_ENDPOINT=your-endpoint.hts
```

### CI/CD Environment
```bash
# CI-safe test run (no credentials required)
pytest -m "unit" --data-source=mocked

# Integration tests with mocked data
pytest -m "integration" --data-source=mocked
```

### Local Development
```bash
# Full test suite with fallback
pytest

# Generate cached fixtures for faster iteration
pytest --update -m "remote and update"

# Work offline with cached data
pytest --data-source=cached
```

## Security Guidelines

### ⚠️ NEVER commit cached data
```bash
# Cached data is in .gitignore
echo "tests/fixture_cache/*.xml" >> .gitignore
```

### ✅ Safe for CI
- Mocked data is anonymized
- No credentials in mocked fixtures
- No sensitive server information

### 🔒 Secure Development
1. Use separate test servers when possible
2. Rotate credentials regularly  
3. Limit remote test frequency
4. Review cached data before sharing

## Developer Workflows

### 🚀 Quick Start (New Developer)
```bash
# 1. Clone repo
git clone https://github.com/HorizonsRC/hurl.git
cd hurl

# 2. Install dependencies
pip install -e .

# 3. Run unit tests (no setup required)
pytest -m unit

# 4. Run integration tests with mocked data
pytest -m integration --data-source=mocked
```

### 🔄 Regular Development
```bash
# Daily development (fast, reliable)
pytest -m "not remote" --data-source=cached

# When changing schemas or adding features
pytest --update -m "remote and update"  # Refresh fixtures
pytest -m integration                   # Validate changes
```

### 🚢 Pre-deployment
```bash
# Full CI simulation
pytest -m "unit" --data-source=mocked

# Integration validation  
pytest -m "integration" --data-source=cached

# Performance regression check
pytest -m "performance" --data-source=cached
```

## Test Data Management

### Generating Mocked Data
```python
# Create anonymized fixtures from real data
def anonymize_xml(real_xml):
    # Replace sensitive values
    return real_xml.replace("Real Site", "Test Site Alpha")
```

### Updating Cached Data
```bash
# Update all cached fixtures
pytest --update -m "remote and update"

# Update specific fixture category
pytest --update tests/test_schemas/test_responses/test_status_response.py
```

### Missing Data Handling
```bash
# Skip gracefully when data unavailable
pytest --skip-missing-data

# See what data sources are available
pytest -v  # Shows data source used for each test
```

## Test Matrix

| Test Type | Mocked | Cached | Remote | CI Safe | Use Case |
|-----------|---------|---------|---------|---------|----------|
| Unit | ✅ | ✅ | ❌ | ✅ | Schema validation, logic |
| Integration | ✅ | ✅ | ✅ | ⚠️* | End-to-end workflows |
| Performance | ⚠️** | ✅ | ✅ | ⚠️** | Latency, regressions |
| Remote Validation | ❌ | ❌ | ✅ | ❌ | Cache refresh |

*\* Integration tests are CI-safe when using mocked data*  
*\*\* Performance tests work with mocked data but prefer real data*

## Troubleshooting

### Common Issues

#### "No data available for {type}/{file}"
```bash
# Solution: Generate missing data or use different source
pytest --data-source=mocked  # Use available mocked data
pytest --update -m remote    # Generate cached data
```

#### "Remote tests require environment variables"
```bash
# Solution: Set required variables
export HILLTOP_BASE_URL="https://your-server.com"
export HILLTOP_HTS_ENDPOINT="endpoint.hts"
```

#### "Connection failed" during --update
```bash
# Solution: Check network and credentials
curl $HILLTOP_BASE_URL/$HILLTOP_HTS_ENDPOINT  # Test connectivity
pytest -m "not remote"                        # Skip remote tests
```

### Debug Information
```bash
# Verbose output shows data source decisions
pytest -v

# See which tests are being skipped and why
pytest -v --skip-missing-data

# Show available test markers
pytest --markers
```

## Contributing New Tests

### Adding Unit Tests
```python
@pytest.mark.unit
@pytest.mark.mocked_data
def test_new_feature(fixture_name):
    """Unit test using mocked data."""
    # Test logic here
```

### Adding Integration Tests
```python
@pytest.mark.integration
def test_integration_workflow(fixture_name):
    """Integration test supporting multiple data sources."""
    # Test workflow here
```

### Creating New Fixtures
```python
# In test file:
@pytest.fixture
def new_fixture(request, httpx_mock, remote_client):
    """New fixture with data source support."""
    manager = TestDataManager(Path(__file__))
    data_file = manager.get_data_file("new_type", "response.xml")
    
    if data_file is None:
        pytest.skip("No test data available")
    
    return data_file.read_text(encoding="utf-8")
```

## Best Practices

### ✅ Do
- Use unit tests for schema validation
- Prefer mocked data for CI
- Update cached fixtures regularly
- Test with multiple data sources
- Add clear test markers

### ❌ Don't  
- Commit cached data to repo
- Hard-code server responses in tests
- Skip environment variable validation
- Assume network connectivity
- Mix test data sources without markers

---

This testing scheme ensures reliable CI/CD while supporting rich local development workflows with real API data.