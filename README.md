# HURL - Hydro URL Generator

A Python client library for interacting with Hilltop Server APIs, developed by Horizons Regional Council as a dependency of [Hydrobot](https://github.com/HorizonsRC/hydrobot). HURL provides a clean, Pythonic interface for fetching environmental and scientific data from Hilltop servers.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0-green)](https://github.com/HorizonsRC/hurl)

## Overview

HURL (Hydro URL Generator) is designed to simplify interactions with Hilltop Server, a platform commonly used for storing and managing environmental data such as water levels, flow rates, rainfall measurements, and other scientific observations. The library handles URL generation, request validation, XML parsing, and provides structured Python objects for easy data manipulation.

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

- Python 3.8 or higher
- Internet connectivity to reach your Hilltop server

### Install from PyPI (Recommended)

```bash
pip install hurl
```

### Install from Source

```bash
git clone https://github.com/HorizonsRC/hurl.git
cd hurl
pip install -e .
```

### Dependencies

HURL requires the following packages:
- `httpx` - HTTP client for making requests
- `pydantic` - Data validation and settings management
- `lxml` - XML processing
- `pandas` - Data manipulation and analysis
- `python-dotenv` - Environment variable management
- `isodate` - ISO date parsing
- `xmltodict` - XML to dictionary conversion

## Quick Start

### Basic Setup

```python
from hurl.client import HilltopClient

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

HURL supports configuration via environment variables:

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
from hurl.client import HilltopClient

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
from hurl.client import HilltopClient
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

HURL provides comprehensive error handling through custom exceptions:

```python
from hurl.client import HilltopClient
from hurl.exceptions import (
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

- `HilltopError` - Base exception for all HURL errors
  - `HilltopConfigError` - Configuration issues (missing URLs, credentials)
  - `HilltopRequestError` - Request validation errors (invalid parameters)
  - `HilltopResponseError` - HTTP and server response errors
  - `HilltopParseError` - XML parsing and data conversion errors

## Validation and Data Types

HURL uses Pydantic for request validation and type safety. Common validation rules:

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

### Development Setup

```bash
# Clone the repository
git clone https://github.com/HorizonsRC/hurl.git
cd hurl

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest pytest-mock

# Run tests
python -m pytest tests/
```

### Running Tests

HURL uses a comprehensive testing strategy that includes both local mocked tests and remote API validation using a fixture cache system.

```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest -m "not remote"  # Skip remote tests
python -m pytest -m "not slow"    # Skip slow tests

# Update fixture cache with latest API responses
python -m pytest --update -m remote
```

#### Testing Strategy & Fixture Cache

HURL implements a sophisticated testing approach using cached API responses to ensure tests remain consistent and fast while still validating against real API behavior:

- **Fixture Cache**: Pre-recorded XML responses from actual Hilltop servers are stored in `tests/fixture_cache/`
- **Remote Validation**: Tests marked with `@pytest.mark.remote` can validate cached responses against live API endpoints
- **Update Mechanism**: The `--update` option makes remote calls to refresh cached responses, ensuring tests track API changes accurately
- **Selective Mocking**: The `httpx_mock` system allows bypassing mocks for specific domains during cache updates

**Example Usage:**
```bash
# Update all cached fixtures from remote APIs
python -m pytest --update -m "remote and update"

# Run tests without making remote calls (uses cached fixtures)
python -m pytest -m "not remote"

# Validate cached responses against remote API (requires connectivity)
python -m pytest -m remote
```

This strategy ensures that:
1. Tests run quickly in CI/CD environments using cached responses
2. API changes are detected when `--update` is run periodically
3. Tests remain reliable even when remote APIs are unavailable
4. Response schema validation stays current with actual API behavior

### Code Style

This project uses:
- Type hints for better code documentation
- Pydantic for data validation
- Black for code formatting (if applicable)
- Comprehensive docstrings

## Model String Representations

All Pydantic models in HURL use a custom YAML-style string representation that provides clean, readable output for debugging and logging.

### YAML-Style Output

All models inherit from `ModelReprMixin`, which provides pretty-printed output:

```python
from hurl.client import HilltopClient

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
from hurl.schemas.mixins import ModelReprMixin

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
- **Repository**: https://github.com/HorizonsRC/hurl

## Acknowledgments

Developed by Horizons Regional Council for environmental data management and analysis. Special thanks to the Hilltop development team for their comprehensive API documentation.

---

**Version**: 0.1.0  
**Python Compatibility**: 3.8+  
**License**: GPL-3.0
