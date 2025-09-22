# WHURL - Hydro URL Generator

WHURL is a Python client library for interacting with Hilltop Server APIs, providing a clean interface for fetching environmental and scientific data from Hilltop servers.

**Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

### Bootstrap, Build, and Test Repository
Run these commands in sequence to set up the development environment:

```bash
# Navigate to repository root
cd /home/runner/work/whurl/whurl

# Install Poetry (if not available) - takes ~30 seconds
curl -sSL https://install.python-poetry.org | python3 -

# Install all dependencies (runtime + development) - takes ~60 seconds. NEVER CANCEL.
poetry install

# Activate the virtual environment
poetry shell

# Run core tests - takes <3 seconds
poetry run python -m pytest tests/ --mode=unit
```

**Fallback pip installation (if Poetry not available):**
```bash
# Install project in development mode - takes ~60 seconds. NEVER CANCEL.
pip install -e .

# Install development dependencies - takes ~30 seconds. NEVER CANCEL.
pip install pytest pytest-mock pytest-httpx

# Install all required runtime dependencies - takes ~90 seconds. NEVER CANCEL.
pip install httpx pydantic lxml pandas python-dotenv isodate xmltodict certifi

# Run core tests - takes <3 seconds
python -m pytest tests/ --mode=unit
```

**CRITICAL TIMING**: 
- Complete setup takes ~2 minutes with Poetry, ~3 minutes with pip
- Individual test runs take <3 seconds
- NEVER CANCEL any install commands - dependency resolution can take time

### Running Tests

**Working Test Commands** (these work reliably):
```bash
# Poetry (Recommended)
poetry run python -m pytest tests/ --mode=offline   # All offline tests (default, works reliably)
poetry run python -m pytest tests/ --mode=unit      # Unit tests only (fastest)

# pip/direct Python (Fallback)
python -m pytest tests/ --mode=offline              # All offline tests (default, works reliably)  
python -m pytest tests/ --mode=unit                 # Unit tests only (fastest)
```

**IMPORTANT**: Default to `--mode=offline` for comprehensive testing. Integration tests fail gracefully when fixture cache is empty, and performance tests run with local mock server.

### Environment Setup for Client Testing

**ALWAYS set these environment variables when testing client functionality:**
```bash
export HILLTOP_BASE_URL="https://data.council.govt.nz"
export HILLTOP_HTS_ENDPOINT="foo.hts"
```

Or create a `.env` file in the repository root:
```env
HILLTOP_BASE_URL=https://data.council.govt.nz
HILLTOP_HTS_ENDPOINT=foo.hts
```

**IMPORTANT**: These variables do not represent a real working API endpoint, and are just for offline testing and debugging.

## Validation

**ALWAYS run these validation steps after making changes:**

### 1. Basic Import Validation
```bash
# Poetry (Recommended)
poetry run python -c "from whurl.client import HilltopClient; print('Import successful!')"

# pip/direct Python (Fallback)
python -c "from whurl.client import HilltopClient; print('Import successful!')"
```

### 2. Client Configuration Validation
```bash
# Without environment variables (should fail with clear error)
poetry run python -c "
from whurl.client import HilltopClient
try:
    client = HilltopClient()
except Exception as e:
    print(f'Expected error: {e}')
"

# With environment variables (should succeed)
HILLTOP_BASE_URL="https://data.council.govt.nz" HILLTOP_HTS_ENDPOINT="foo.hts" poetry run python -c "
from whurl.client import HilltopClient
client = HilltopClient()
print(f'Client created: {client.base_url}')
print(f'Endpoint: {client.hts_endpoint}')
print(f'Timeout: {client.timeout}')
"
```

### 3. Core Test Suite Validation
```bash
# This should always pass in <3 seconds
poetry run python -m pytest tests/ --mode=offline --quiet
```

### 4. Complete Library Validation Scenario
**ALWAYS run this complete validation after making changes:**

```bash
HILLTOP_BASE_URL="https://data.council.govt.nz" HILLTOP_HTS_ENDPOINT="foo.hts" poetry run python -c "
# Complete validation scenario
from whurl.client import HilltopClient

print('=== Complete WHURL Library Validation ===')

# Test 1: Client creation and configuration
print('1. Testing client creation...')
client = HilltopClient()
print(f'   ✓ Client created successfully')
print(f'   ✓ Base URL: {client.base_url}')
print(f'   ✓ Endpoint: {client.hts_endpoint}')
print(f'   ✓ Timeout: {client.timeout}')

# Test 2: Context manager support  
print('2. Testing context manager...')
with HilltopClient() as ctx_client:
    print(f'   ✓ Context manager works')
    print(f'   ✓ Client has session: {hasattr(ctx_client, \"session\")}')

# Test 3: Import all key components
print('3. Testing imports...')
from whurl.exceptions import HilltopError, HilltopConfigError
from whurl.schemas.requests import StatusRequest
from whurl.utils import validate_hilltop_interval_notation
print('   ✓ All key imports successful')

# Test 4: Request validation
print('4. Testing request validation...')
status_req = StatusRequest(
    base_url='https://test.com', 
    hts_endpoint='test.hts'
)
url = status_req.gen_url()
print(f'   ✓ Request generation works: {url}')

print()
print('=== VALIDATION COMPLETE ===')
print('✓ Library is fully functional and ready for development')
"
```

**Expected Output**: Should show all checkmarks and complete successfully.

**CRITICAL**: You can create and test client instances, but actual API calls require network connectivity to live Hilltop servers. For testing changes, rely on the mocked test suite and this validation scenario.

## Common Tasks

### Repository Structure
```
/home/runner/work/whurl/whurl/           # Repository root
├── whurl/                              # Main Python package  
│   ├── client.py                      # Main HilltopClient class
│   ├── exceptions.py                  # Custom exceptions
│   ├── schemas/                       # Request/Response schemas
│   └── utils.py                       # Utility functions
├── tests/                             # Test directory
│   ├── test_utils.py                 # Utility tests
│   ├── test_schemas/test_requests/   # Request validation tests
│   ├── test_schemas/test_responses/  # Response tests
│   ├── fixture_cache/                # Cached API responses for testing
│   └── conftest.py                   # Shared test fixtures
├── pyproject.toml                    # Modern Python project config
├── README.md                         # Comprehensive documentation
└── config.yaml                       # Configuration file
```

### Key Files to Check After Changes
- **`whurl/client.py`**: Main client implementation
- **`whurl/schemas/`**: When changing API request/response handling
- **`tests/test_schemas/`**: When adding new request/response types
- **`__init__.py` files: When adding new request/response types
- **Environment variables**: Always test both with and without `HILLTOP_BASE_URL`

### Dependencies Reference
**Runtime**: httpx, pydantic, lxml, pandas, python-dotenv, isodate, xmltodict, certifi, pyyaml, fastapi, uvicorn
**Development**: pytest, pytest-mock, pytest-httpx, pytest-benchmark, pytest-asyncio, pytest-cov

## Testing Strategy & Fixture Cache

WHURL uses a sophisticated testing approach:

- **Unit Tests**: Fast, isolated tests using mocked data from `tests/mocked_data/`
- **Integration Tests**: Tests that use cached fixtures from `tests/fixture_cache/` 
- **Performance Tests**: HTTP performance validation using `tests/performance/`
- **Remote Tests**: Tests that validate against live APIs (marked `@pytest.mark.remote`)

**Test Modes:**
```bash
# Poetry (Recommended)
poetry run python -m pytest tests/ --mode=unit          # Unit tests only (always offline)
poetry run python -m pytest tests/ --mode=offline       # All offline tests (may fail if fixtures missing)
poetry run python -m pytest tests/ --mode=integration   # Integration tests only
poetry run python -m pytest tests/ --mode=performance   # Performance tests only

# pip/direct Python (Fallback)
python -m pytest tests/ --mode=unit                     # Unit tests only (always offline)
python -m pytest tests/ --mode=offline                  # All offline tests (may fail if fixtures missing)
```

**Remote testing** (requires network connectivity):
```bash
# Set environment variables for real endpoints first
export HILLTOP_BASE_URL="https://real-hilltop-server.com"
export HILLTOP_HTS_ENDPOINT="real.hts"

# Update cached fixtures from remote APIs (may take 10-30 seconds)
poetry run python -m pytest --update --mode=integration
```

## Critical Warnings

### Environment Dependencies
- **Client instantiation requires** environment variables or will fail with: "Base URL must be provided or set in environment variables"

### Performance Expectations
- **Setup**: ~2 minutes with Poetry, ~3 minutes with pip
- **Unit tests**: <3 seconds consistently
- **Integration tests**: 10-30 seconds (if fixture files present)
- **Remote tests**: 10-30 seconds (if network accessible)

## Application Type & Usage

This is a **client library**, not an application with a UI. It provides:
- Python wrapper for Hilltop Server XML APIs
- Pydantic-based request validation
- Automatic XML parsing to Python objects
- Context manager support for proper resource cleanup

**Example Usage Pattern**:
```python
from whurl.client import HilltopClient

# Always use environment variables for configuration
with HilltopClient() as client:
    status = client.get_status()
    sites = client.get_site_list()
    measurements = client.get_measurement_list(site="SiteName")
```

## When Things Go Wrong

### Import Errors
- Run: `poetry install` or install all dependencies listed above
- Check: Python path and virtual environment

### Test Failures
- Run unit tests only: `poetry run python -m pytest tests/ --mode=unit`
- Clean cache: `find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true`
- For integration test failures: Check if fixture cache files exist in `tests/fixture_cache/`

### Client Configuration Errors  
- Set `HILLTOP_BASE_URL` and `HILLTOP_HTS_ENDPOINT` environment variables
- Verify with the validation commands above

### Network/Remote Test Issues
- Remote tests require internet connectivity
- Use unit tests for offline development: `--mode=unit`
- Skip remote tests: `-m "not remote"`
