# WHURL - Which Hydro URL

A Python client library for interacting with Hilltop Server APIs, developed by Horizons Regional Council as a dependency of [Hydrobot](https://github.com/HorizonsRC/hydrobot). WHURL provides a clean, Pythonic interface for fetching environmental and scientific data from Hilltop servers.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/dependency%20management-Poetry-blue)](https://python-poetry.org/)
[![Version](https://img.shields.io/badge/version-0.1.0-green)](https://github.com/HorizonsRC/whurl)

## Overview

WHURL (Which Hydro URL) is designed to simplify interactions with Hilltop Server, a platform commonly used for storing and managing environmental data such as water levels, flow rates, rainfall measurements, and other scientific observations. The library handles URL generation, request validation, XML parsing, and provides structured Python objects for easy data manipulation.

> **⚠️ Work in Progress**: This library is currently under active development. While core functionality is stable and tested, not all Hilltop API endpoints are supported yet. See the [Planned Features](#planned-features) section for upcoming enhancements.

### Key Features

- **Simple Client Interface**: Easy-to-use `HilltopClient` with methods for all major Hilltop operations
- **Request Validation**: Pydantic-based validation ensures proper request formatting
- **Type Safety**: Full type hints for better IDE support and code reliability
- **XML Response Parsing**: Automatic parsing of Hilltop XML responses into Python objects
- **Error Handling**: Comprehensive exception handling with detailed error messages
- **Configuration Management**: Support for environment variables and direct configuration
- **Context Manager Support**: Proper resource cleanup with `with` statement support

## Planned Features

The following features are planned for future releases:

- **WFS (Web Feature Service) Support**: Integration with WFS endpoints for geospatial data access
- **SOS (Sensor Observation Service) Calls**: Support for OGC SOS standard endpoints
- **Kisters KiWIS Integration**: Native support for Kisters KiWIS (Kisters Water Information System) APIs
- **Web Frontend Interface**: A user-friendly web interface featuring:
  - Interactive dropdown menus for site and measurement selection
  - Dynamic URL construction based on user selections
  - "Download as" functionality for various output formats (CSV, JSON, XML)
  - Real-time data preview capabilities

## Installation

### Prerequisites

- Python 3.11 or higher
- [Poetry](https://python-poetry.org/) for dependency management
- Internet connectivity to reach your Hilltop server

### Install from PyPI (Recommended)

```bash
pip install whurl
```

### Development Installation with Poetry

For development or contributing to WHURL, use Poetry for dependency management:

```bash
# Clone the repository
git clone https://github.com/HorizonsRC/whurl.git
cd whurl

# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies and WHURL in development mode
poetry install

# Activate the virtual environment
poetry shell
```

### Legacy pip Installation from Source

```bash
git clone https://github.com/HorizonsRC/whurl.git
cd whurl
pip install -e .
```

### Dependencies

WHURL requires the following packages (automatically managed by Poetry):
- `httpx` - HTTP client for making requests
- `pydantic` - Data validation and settings management
- `lxml` - XML processing
- `pandas` - Data manipulation and analysis
- `python-dotenv` - Environment variable management
- `isodate` - ISO date parsing
- `xmltodict` - XML to dictionary conversion
- `pyyaml` - YAML processing for configuration

### Why Poetry?

WHURL uses [Poetry](https://python-poetry.org/) as the standard for dependency management and packaging for several important reasons:

#### **Reproducible Builds**
Poetry locks all dependencies (including transitive dependencies) to specific versions in `poetry.lock`, ensuring that all developers and CI/CD systems use exactly the same package versions.

#### **Simplified Dependency Management**
- **Add dependencies**: `poetry add package-name`
- **Development dependencies**: `poetry add --group dev package-name`
- **Remove dependencies**: `poetry remove package-name`
- **Update dependencies**: `poetry update`

#### **Isolated Virtual Environments**
Poetry automatically creates and manages virtual environments, preventing dependency conflicts between projects.

#### **Modern Python Packaging**
Poetry uses the modern `pyproject.toml` standard (PEP 621) instead of legacy `setup.py` and `requirements.txt` files, providing better metadata management and build configuration.

#### **Developer Experience**
- `poetry shell` - Activate virtual environment
- `poetry run command` - Run commands in the Poetry environment
- `poetry show` - View installed packages and their dependencies
- `poetry build` - Build distribution packages for PyPI

#### **For Contributors**
If you're contributing to WHURL, Poetry ensures that:
1. Your development environment exactly matches other contributors
2. New dependencies are properly locked and tracked
3. The build and test process is consistent across all environments
4. Package installation and distribution follows modern Python standards

## Quick Start

### Basic Setup

```python
from whurl.client import HilltopClient

# Option 1: Direct configuration
client = HilltopClient(
    base_url="https://your-hilltop-server.com",
    hts_endpoint="data.hts",
    timeout=60  # Optional, defaults to 60 seconds
)

# Option 2: Using environment variables
# Set HILLTOP_BASE_URL and HILLTOP_HTS_ENDPOINT
client = HilltopClient()

# Always use as a context manager for proper cleanup
with client:
    # Your code here
    status = client.get_status()
    print(f"Server status: {status}")
```

### Environment Variables

WHURL supports configuration via environment variables:

```bash
export HILLTOP_BASE_URL="https://your-hilltop-server.com"
export HILLTOP_HTS_ENDPOINT="data.hts"
```

Or create a `.env` file:
```env
HILLTOP_BASE_URL=https://your-hilltop-server.com
HILLTOP_HTS_ENDPOINT=data.hts
```

### Simple Example

```python
from whurl.client import HilltopClient

with HilltopClient() as client:
    # Get server status
    status = client.get_status()
    print(f"Server is running: {status.server}")
    
    # List all sites
    sites = client.get_site_list()
    print(f"Found {len(sites.sites)} sites")
    
    # Get measurements for a specific site
    measurements = client.get_measurement_list(site="YourSiteName")
    for measurement in measurements.measurements:
        print(f"Measurement: {measurement.name}, Units: {measurement.units}")
```

## API Reference

### HilltopClient

The main client class for interacting with Hilltop servers.

#### Constructor

```python
HilltopClient(
    base_url: str | None = None,
    hts_endpoint: str | None = None, 
    timeout: int = 60
)
```

**Parameters:**
- `base_url`: The base URL of your Hilltop server (e.g., "https://data.council.govt.nz")
- `hts_endpoint`: The HTS endpoint path (e.g., "foo.hts")
- `timeout`: Request timeout in seconds (default: 60)

### Client Methods

#### get_status()
Get the status of the Hilltop server.

```python
status = client.get_status()
print(status.server)  # Server information
print(status.version)  # Hilltop version
```

**Returns:** `StatusResponse` object

#### get_site_list(**kwargs)
Retrieve a list of sites from the Hilltop server.

```python
# Get all sites
sites = client.get_site_list()

# Get sites with location information
sites = client.get_site_list(location="Yes")

# Filter by measurement type
sites = client.get_site_list(measurement="Flow")

# Filter by collection
sites = client.get_site_list(collection="River")
```

**Parameters:**
- `location`: "Yes", "LatLong", or None - Include location data
- `measurement`: Filter sites by measurement type
- `collection`: Filter sites by collection name
- `site_parameters`: Include site parameters
- `bounding_box`: Spatial filter (format: "x1,y1,x2,y2")

**Returns:** `SiteListResponse` object

#### get_measurement_list(**kwargs)
Get available measurements for a site or collection.

```python
# Get measurements for a specific site
measurements = client.get_measurement_list(site="YourSiteName")

# Get measurements with units information
measurements = client.get_measurement_list(site="YourSiteName", units="Yes")

# Get measurements for a collection
measurements = client.get_measurement_list(collection="River")
```

**Parameters:**
- `site`: Site name (required if collection not specified)
- `collection`: Collection name
- `units`: "Yes" to include units information

**Returns:** `MeasurementListResponse` object

#### get_site_info(**kwargs)
Get detailed information about a specific site.

```python
site_info = client.get_site_info(site="YourSiteName")
print(site_info.site_name)
print(site_info.location)
```

**Parameters:**
- `site`: Site name (required)

**Returns:** `SiteInfoResponse` object

#### get_data(**kwargs)
Retrieve measurement data from the Hilltop server.

```python
# Get recent data
data = client.get_data(
    site="YourSiteName",
    measurement="Flow",
    from_datetime="2024-01-01T00:00:00",
    to_datetime="2024-01-31T23:59:59"
)

# Get data with statistics
data = client.get_data(
    site="YourSiteName",
    measurement="Flow", 
    method="Average",
    interval="1 day"
)

# Get data with custom time intervals
data = client.get_data(
    site="YourSiteName",
    measurement="Rainfall",
    time_interval="1 hour",
    alignment="00:00"
)
```

**Parameters:**
- `site`: Site name
- `measurement`: Measurement name  
- `from_datetime`: Start datetime (ISO format)
- `to_datetime`: End datetime (ISO format)
- `method`: Statistical method ("Interpolate", "Average", "Total", "Moving Average", "EP", "Extrema")
- `interval`: Time interval for statistics (e.g., "1 day", "4 hours")
- `time_interval`: Regular time interval for data
- `alignment`: Time alignment (e.g., "00:00")
- `collection`: Collection name
- `gap_tolerance`: Maximum gap between data points
- `format`: Output format ("Native" or other formats)

**Returns:** `GetDataResponse` object

#### get_time_range(**kwargs)
Get the available time range for a measurement at a site.

```python
time_range = client.get_time_range(
    site="YourSiteName",
    measurement="Flow"
)
print(f"Data available from {time_range.from_time} to {time_range.to_time}")
```

**Parameters:**
- `site`: Site name (required)
- `measurement`: Measurement name (required)
- `format`: "json" for JSON response, omit for XML

**Returns:** `TimeRangeResponse` object

#### get_collection_list(**kwargs)
Get a list of available collections.

```python
collections = client.get_collection_list()
for collection in collections.collections:
    print(f"Collection: {collection.name}")
```

**Returns:** `CollectionListResponse` object

## Usage Examples

### Environmental Data Monitoring

```python
from whurl.client import HilltopClient
import pandas as pd

with HilltopClient() as client:
    # Monitor water levels at multiple sites
    sites = ["Site1", "Site2", "Site3"]
    water_levels = {}
    
    for site in sites:
        data = client.get_data(
            site=site,
            measurement="Water Level",
            from_datetime="2024-01-01T00:00:00",
            to_datetime="2024-01-31T23:59:59"
        )
        water_levels[site] = data.to_dataframe()  # Convert to pandas DataFrame
    
    # Analyze the data
    for site, df in water_levels.items():
        print(f"{site}: Max level = {df['Value'].max():.2f} m")
```

### Rainfall Analysis

```python
with HilltopClient() as client:
    # Get hourly rainfall data
    rainfall = client.get_data(
        site="RainfallSite",
        measurement="Rainfall",
        method="Total",
        interval="1 hour",
        from_datetime="2024-01-01T00:00:00",
        to_datetime="2024-01-07T23:59:59"
    )
    
    # Calculate daily totals
    daily_rain = client.get_data(
        site="RainfallSite", 
        measurement="Rainfall",
        method="Total",
        interval="1 day",
        from_datetime="2024-01-01T00:00:00",
        to_datetime="2024-01-31T23:59:59"
    )
```

### Site Discovery and Exploration

```python
with HilltopClient() as client:
    # Discover sites with flow measurements
    sites = client.get_site_list(measurement="Flow", location="LatLong")
    
    for site in sites.sites:
        print(f"Site: {site.name}")
        print(f"Location: {site.latitude}, {site.longitude}")
        
        # Get available measurements
        measurements = client.get_measurement_list(site=site.name, units="Yes")
        for measurement in measurements.measurements:
            print(f"  - {measurement.name} ({measurement.units})")
        
        # Get data time range
        time_range = client.get_time_range(site=site.name, measurement="Flow")
        print(f"  Data: {time_range.from_time} to {time_range.to_time}")
        print()
```

## Error Handling

WHURL provides comprehensive error handling through custom exceptions:

```python
from whurl.client import HilltopClient
from whurl.exceptions import (
    HilltopError, 
    HilltopConfigError, 
    HilltopRequestError,
    HilltopResponseError,
    HilltopParseError
)

try:
    with HilltopClient() as client:
        data = client.get_data(site="InvalidSite", measurement="Flow")
        
except HilltopConfigError as e:
    print(f"Configuration error: {e}")
    # Handle missing base_url or hts_endpoint
    
except HilltopRequestError as e:
    print(f"Request error: {e}")
    # Handle invalid parameters
    
except HilltopResponseError as e:
    print(f"Server error: {e}")
    # Handle HTTP errors or server-side issues
    
except HilltopParseError as e:
    print(f"Parse error: {e}")
    # Handle XML parsing errors
    
except HilltopError as e:
    print(f"General Hilltop error: {e}")
    # Handle any other Hilltop-related errors
```

### Exception Hierarchy

- `HilltopError` - Base exception for all WHURL errors
  - `HilltopConfigError` - Configuration issues (missing URLs, credentials)
  - `HilltopRequestError` - Request validation errors (invalid parameters)
  - `HilltopResponseError` - HTTP and server response errors
  - `HilltopParseError` - XML parsing and data conversion errors

## Validation and Data Types

WHURL uses Pydantic for request validation and type safety. Common validation rules:

### Time Intervals
```python
# Valid time interval formats
"10 seconds"    # or "10 second", "10s"
"5 minutes"     # or "5 minute", "5m" 
"1 hour"        # or "1h"
"1 day"         # or "1d"
"1 week"        # or "1w"
"1 month"       # or "1mo"
"1 year"        # or "1y"
```

### Date Formats
```python
# ISO 8601 format required
"2024-01-01T00:00:00"
"2024-12-31T23:59:59"
```

### Statistical Methods
- `"Interpolate"` - Interpolated values
- `"Average"` - Average over interval
- `"Total"` - Sum over interval  
- `"Moving Average"` - Moving average
- `"EP"` - End period
- `"Extrema"` - Min/max values

## Development and Contributing

WHURL uses [Poetry](https://python-poetry.org/) for dependency management and packaging. This ensures reproducible builds and simplifies development workflows.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/HorizonsRC/whurl.git
cd whurl

# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install all dependencies (runtime + development)
poetry install

# Activate the virtual environment
poetry shell

# Run tests to verify setup
poetry run python -m pytest tests/ -m 'not remote'
```

### Poetry Commands

```bash
# Install dependencies
poetry install

# Add a new dependency
poetry add package-name

# Add a development dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Run commands in the Poetry environment
poetry run python script.py
poetry run pytest

# Activate virtual environment
poetry shell

# Show installed packages
poetry show

# Build package for distribution
poetry build
```

### Legacy pip Development Setup

If you prefer using pip directly:

```bash
# Clone the repository
git clone https://github.com/HorizonsRC/whurl.git
cd whurl

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest pytest-mock pytest-httpx

# Run tests
python -m pytest tests/
```

### Running Tests

WHURL uses a comprehensive testing strategy that includes both local mocked tests and remote API validation using a fixture cache system. For detailed information about testing categories, modes, and troubleshooting, see the [Testing Strategy Documentation](docs/TESTING_STRATEGY.md).

#### Quick Start - Testing

```bash
# Poetry (Recommended) - Fast unit tests for daily development
poetry run python -m pytest tests/ --mode=unit

# Legacy pip - Fast unit tests for daily development  
python -m pytest tests/ --mode=unit

# All offline tests (may fail if cached fixtures missing)
poetry run python -m pytest tests/ --mode=offline
```

#### Environment Setup for Testing

Some tests require environment variables to be set:

```bash
export HILLTOP_BASE_URL="https://data.council.govt.nz"
export HILLTOP_HTS_ENDPOINT="foo.hts"
```

Or create a `.env` file in the project root:
```env
HILLTOP_BASE_URL=https://data.council.govt.nz
HILLTOP_HTS_ENDPOINT=foo.hts
```

*Note: These are example values for testing - they do not represent a real working API endpoint.*

#### Test Categories

**Unit Tests** (fastest, always offline):
```bash
# Poetry (Recommended)
poetry run python -m pytest tests/ --mode=unit

# pip/direct Python
python -m pytest tests/ --mode=unit
```

**Integration Tests** (use cached API fixtures):
```bash
# Poetry (Recommended)
poetry run python -m pytest tests/ --mode=integration

# pip/direct Python  
python -m pytest tests/ --mode=integration
```

**Performance Tests** (HTTP client validation):
```bash
# Performance tests require explicit flags
poetry run python -m pytest tests/performance/ --performance-local
```

**Remote Tests** (live API validation):
```bash
# Set real API endpoints first
export HILLTOP_BASE_URL="https://real-server.com"
export HILLTOP_HTS_ENDPOINT="real.hts"

# Update cached fixtures from remote APIs
poetry run python -m pytest --update --mode=integration
```

For complete testing documentation including troubleshooting, fixture cache management, and performance testing details, see the [Testing Strategy Documentation](docs/TESTING_STRATEGY.md).

### Code Style

This project uses:
- Type hints for better code documentation
- Pydantic for data validation
- Black for code formatting (if applicable)
- Comprehensive docstrings

## Model String Representations

All Pydantic models in WHURL use a custom YAML-style string representation that provides clean, readable output for debugging and logging.

### YAML-Style Output

All models inherit from `ModelReprMixin`, which provides pretty-printed output:

```python
from whurl.client import HilltopClient

with HilltopClient() as client:
    # Get data request shows clean YAML output
    data = client.get_data(
        site="YourSiteName",
        measurement="Flow",
        from_datetime="2023-01-01T00:00:00"
    )
    
    print(str(data))
    # Output:
    # GetDataResponse:
    #   agency: Your Agency
    #   measurement:
    #   - site_name: YourSiteName
    #     data_source:
    #       name: Flow DataSource
    #       num_items: 1
    #       ts_type: StdSeries
    #       data_type: Flow
    #       interpolation: Discrete
    #       item_info:
    #       - item_number: 1
    #         item_name: Flow
    #         item_format: F2
    #         units: m³/s
    #         format: F
    #     data:
    #       date_format: Calendar
    #       num_items: 100
    #       timeseries: '<DataFrame: 100 rows × 1 columns>'
```

### Features of Model Representations

- **Headers**: Each model output starts with the model class name
- **Nested Models**: Recursive formatting of nested objects with proper indentation
- **Lists**: Clean formatting of lists and collections  
- **Null Exclusion**: None/null values are automatically excluded for cleaner output
- **DataFrame Handling**: Pandas DataFrames show summary information instead of raw data
- **YAML Valid**: Output can be parsed as valid YAML

### Including Null Values

For specific use cases where you need to show None/null values, define `repr_include_unset` in your model:

```python
from typing import ClassVar, Set
from pydantic import BaseModel
from whurl.schemas.mixins import ModelReprMixin

class CustomModel(ModelReprMixin, BaseModel):
    repr_include_unset: ClassVar[Set[str]] = {"important_field"}
    
    name: str
    optional_field: str = None      # Will be excluded
    important_field: str = None     # Will be included even if None
    
model = CustomModel(name="test")
print(str(model))
# CustomModel:
#   name: test
#   important_field: null
```

This makes debugging and logging much more readable compared to default Pydantic output.

## Configuration Reference

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `HILLTOP_BASE_URL` | Base URL of Hilltop server | `https://data.council.govt.nz` |
| `HILLTOP_HTS_ENDPOINT` | HTS endpoint file | `foo.hts` |

### Client Configuration

```python
client = HilltopClient(
    base_url="https://your-server.com",  # Required
    hts_endpoint="data.hts",             # Required  
    timeout=60                           # Optional, default 60 seconds
)
```

## Troubleshooting

### Common Issues

**1. Configuration Errors**
```
HilltopConfigError: Base URL must be provided or set in environment variables
```
Solution: Set `HILLTOP_BASE_URL` and `HILLTOP_HTS_ENDPOINT` environment variables or pass them to the client constructor.

**2. Connection Timeouts**
```
HilltopResponseError: HTTP error occurred: timeout
```
Solution: Increase timeout value or check network connectivity.

**3. Invalid Parameters**
```
HilltopRequestError: Method must be specified when Interval is specified
```
Solution: Ensure required parameters are provided when using statistical methods.

**4. SSL/Certificate Issues**
Note: Current version disables SSL verification for testing. For production, ensure proper SSL certificates.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contact and Support

- **Author**: Nic Mostert
- **Email**: nicolas.mostert@horizons.govt.nz
- **Organization**: Horizons Regional Council
- **Repository**: https://github.com/HorizonsRC/whurl

## Acknowledgments

Developed by Horizons Regional Council for environmental data management and analysis. Special thanks to the Hilltop development team for their comprehensive API documentation.

---

**Version**: 0.1.0  
**Python Compatibility**: 3.11+  
**License**: GPL-3.0
