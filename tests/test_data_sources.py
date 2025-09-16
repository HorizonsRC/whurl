"""Test data source configuration and utilities for HURL testing.

This module implements the advanced test scheme supporting three data sources:
1. Mocked Data: Anonymized XML fixtures checked into repo (CI-safe)
2. Cached Data: Local cache of real remote data (dev iteration)
3. Remote Data: Direct live API calls (fixture refresh/validation)
"""

import os
from enum import Enum
from pathlib import Path
from typing import Optional
import pytest


class TestDataSource(Enum):
    """Available test data sources."""
    MOCKED = "mocked"        # Anonymized data checked into repo
    CACHED = "cached"        # Local cache of remote data  
    REMOTE = "remote"        # Direct API calls


class TestDataManager:
    """Manages test data sources and provides fallback logic."""
    
    def __init__(self, test_file_path: Path):
        """Initialize with the test file path to determine data directories."""
        self.test_root = test_file_path.parent.parent.parent
        self.mocked_dir = self.test_root / "mocked_data"
        self.cached_dir = self.test_root / "fixture_cache"
    
    def get_data_file(self, data_type: str, filename: str, 
                     source: Optional[TestDataSource] = None) -> Optional[Path]:
        """Get the appropriate data file based on source preference and availability.
        
        Args:
            data_type: Type of data (e.g., 'status', 'site_list', etc.)
            filename: Name of the XML file
            source: Preferred data source, or None for auto-selection
            
        Returns:
            Path to the data file, or None if not found
        """
        if source == TestDataSource.REMOTE:
            # Remote data is handled differently (not file-based)
            return None
            
        # Define search order based on preference
        if source == TestDataSource.CACHED:
            search_paths = [
                self.cached_dir / data_type / filename,
                self.mocked_dir / data_type / filename,
            ]
        elif source == TestDataSource.MOCKED:
            search_paths = [
                self.mocked_dir / data_type / filename,
            ]
        else:
            # Auto-selection: prefer cached, fallback to mocked
            search_paths = [
                self.cached_dir / data_type / filename,
                self.mocked_dir / data_type / filename,
            ]
        
        for path in search_paths:
            if path.exists():
                return path
                
        return None
    
    def get_available_sources(self, data_type: str, filename: str) -> list[TestDataSource]:
        """Get list of available data sources for given data type and file."""
        sources = []
        
        # Check mocked data
        if (self.mocked_dir / data_type / filename).exists():
            sources.append(TestDataSource.MOCKED)
            
        # Check cached data  
        if (self.cached_dir / data_type / filename).exists():
            sources.append(TestDataSource.CACHED)
            
        # Remote is always theoretically available (though may fail)
        sources.append(TestDataSource.REMOTE)
        
        return sources


def get_test_data_manager(test_file_path: str) -> TestDataManager:
    """Get a TestDataManager instance for the given test file."""
    return TestDataManager(Path(test_file_path))


def skip_if_no_data_source(data_type: str, filename: str, test_file_path: str, 
                          preferred_source: Optional[TestDataSource] = None):
    """Decorator to skip test if required data source is not available."""
    manager = get_test_data_manager(test_file_path)
    
    if preferred_source == TestDataSource.REMOTE:
        # Remote tests require environment variables
        if not (os.getenv("HILLTOP_BASE_URL") and os.getenv("HILLTOP_HTS_ENDPOINT")):
            return pytest.mark.skip(
                reason="Remote tests require HILLTOP_BASE_URL and HILLTOP_HTS_ENDPOINT environment variables"
            )
        return lambda func: func
    
    data_file = manager.get_data_file(data_type, filename, preferred_source)
    if data_file is None:
        available_sources = manager.get_available_sources(data_type, filename)
        return pytest.mark.skip(
            reason=f"No data available for {data_type}/{filename}. "
                   f"Available sources: {[s.value for s in available_sources]}"
        )
    
    return lambda func: func


def create_fixture_with_fallback(data_type: str, filename: str, 
                               request_class_import: str, request_kwargs: dict):
    """Factory function to create fixtures with fallback logic.
    
    This creates a fixture function that:
    1. Tries to use cached data if available
    2. Falls back to mocked data
    3. Supports remote data updates via --update flag
    4. Handles missing data gracefully
    """
    
    def fixture_func(request, httpx_mock, remote_client):
        test_file_path = Path(request.fspath)
        manager = get_test_data_manager(str(test_file_path))
        
        # Handle remote data updates
        if request.config.getoption("--update"):
            return _handle_remote_update(
                data_type, filename, request_class_import, request_kwargs,
                httpx_mock, remote_client, manager
            )
        
        # Try to get data file with fallback
        data_file = manager.get_data_file(data_type, filename)
        
        if data_file is None:
            pytest.skip(f"No test data available for {data_type}/{filename}")
        
        return data_file.read_text(encoding="utf-8")
    
    return fixture_func


def _handle_remote_update(data_type: str, filename: str, request_class_import: str, 
                         request_kwargs: dict, httpx_mock, remote_client, 
                         manager: TestDataManager):
    """Handle remote data updates for fixture cache."""
    from urllib.parse import urlparse
    
    # Import the request class dynamically
    module_path, class_name = request_class_import.rsplit('.', 1)
    module = __import__(module_path, fromlist=[class_name])
    request_class = getattr(module, class_name)
    
    # Switch off httpx mock for remote requests
    httpx_mock._options.should_mock = (
        lambda request: request.url.host != urlparse(remote_client.base_url).netloc
    )
    
    # Create request and fetch remote data
    remote_request = request_class(
        base_url=remote_client.base_url,
        hts_endpoint=remote_client.hts_endpoint,
        **request_kwargs
    )
    remote_url = remote_request.gen_url()
    remote_xml = remote_client.session.get(remote_url).text
    
    # Save to cache
    cache_path = manager.cached_dir / data_type / filename
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(remote_xml, encoding="utf-8")
    
    return remote_xml