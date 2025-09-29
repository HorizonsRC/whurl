from datetime import datetime, timedelta
from unittest.mock import Mock
from whurl.cache import DomainCache, CacheEntry, normalize_name
from whurl.schemas.responses.measurement_list import MeasurementListResponse
from whurl.schemas.responses.site_list import SiteListResponse
import pytest

"""Tests for the domain cache module."""




class TestNormalizeName:
    """Test the normalize_name function."""

    def test_basic_normalization(self):
        """Test basic name normalization."""
        assert normalize_name("Site Name") == "site name"
        assert normalize_name("  SITE   NAME  ") == "site name"
        assert normalize_name("Site\t\nName") == "site name"

    def test_ascii_folding(self):
        """Test ASCII folding normalization."""
        assert normalize_name("Café", ascii_fold=True) == "cafe"
        assert normalize_name("Naïve", ascii_fold=True) == "naive"
        assert normalize_name("Café", ascii_fold=False) == "café"

    def test_empty_string(self):
        """Test empty string normalization."""
        assert normalize_name("") == ""
        assert normalize_name("   ") == ""

    def test_special_characters(self):
        """Test special character handling."""
        assert normalize_name("Site-Name_123") == "site-name_123"
        assert normalize_name("Site.Name@Domain") == "site.name@domain"


class TestCacheEntry:
    """Test the CacheEntry dataclass."""

    def test_basic_creation(self):
        """Test basic cache entry creation."""
        data = {"test": "data"}
        timestamp = datetime.utcnow()
        entry = CacheEntry(data=data, timestamp=timestamp)
        
        assert entry.data == data
        assert entry.timestamp == timestamp
        assert entry.etag is None
        assert entry.last_modified is None
        assert entry.expires is None

    def test_with_metadata(self):
        """Test cache entry with HTTP cache metadata."""
        data = {"test": "data"}
        timestamp = datetime.utcnow()
        expires = timestamp + timedelta(hours=1)
        
        entry = CacheEntry(
            data=data,
            timestamp=timestamp,
            etag='"abc123"',
            last_modified="Wed, 21 Oct 2015 07:28:00 GMT",
            expires=expires
        )
        
        assert entry.etag == '"abc123"'
        assert entry.last_modified == "Wed, 21 Oct 2015 07:28:00 GMT"
        assert entry.expires == expires

    def test_expiry_check(self):
        """Test cache entry expiry checking."""
        past_time = datetime.utcnow() - timedelta(hours=1)
        future_time = datetime.utcnow() + timedelta(hours=1)
        
        # Entry without expiry
        entry_no_expire = CacheEntry(data={}, timestamp=datetime.utcnow())
        assert not entry_no_expire.is_expired

        # Entry with past expiry
        entry_expired = CacheEntry(
            data={}, 
            timestamp=datetime.utcnow(),
            expires=past_time
        )
        assert entry_expired.is_expired

        # Entry with future expiry
        entry_valid = CacheEntry(
            data={}, 
            timestamp=datetime.utcnow(),
            expires=future_time
        )
        assert not entry_valid.is_expired


class TestDomainCache:
    """Test the DomainCache class."""

    @pytest.fixture
    def cache(self):
        """Create a domain cache instance."""
        return DomainCache(default_ttl=timedelta(hours=1))

    @pytest.fixture
    def mock_site_response(self):
        """Create a mock site list response."""
        mock_response = Mock(spec=SiteListResponse)
        
        # Create mock sites
        mock_site1 = Mock()
        mock_site1.name = "Test Site 1"
        mock_site1.easting = 1234567.0
        mock_site1.northing = 7654321.0
        
        mock_site2 = Mock()
        mock_site2.name = "Test Site 2"
        mock_site2.easting = 1234568.0
        mock_site2.northing = 7654322.0
        
        mock_response.site_list = [mock_site1, mock_site2]
        return mock_response

    @pytest.fixture
    def mock_measurement_response(self):
        """Create a mock measurement list response."""
        mock_response = Mock(spec=MeasurementListResponse)
        
        # Create mock data source
        mock_data_source = Mock()
        mock_data_source.site = "Test Site 1"
        
        # Create mock measurements
        mock_measurement1 = Mock()
        mock_measurement1.name = "Flow"
        mock_measurement1.units = "m³/s"
        
        mock_measurement2 = Mock()
        mock_measurement2.name = "Water Level"
        mock_measurement2.units = "m"
        
        mock_data_source.measurements = [mock_measurement1, mock_measurement2]
        mock_response.data_sources = [mock_data_source]
        return mock_response

    def test_initialization(self, cache):
        """Test cache initialization."""
        assert cache.default_ttl == timedelta(hours=1)
        assert not cache.ascii_fold
        assert not cache.sites_cache_valid
        assert not cache.measurements_cache_valid

    def test_refresh_sites(self, cache, mock_site_response):
        """Test refreshing sites cache."""
        etag = '"abc123"'
        last_modified = "Wed, 21 Oct 2015 07:28:00 GMT"
        
        cache.refresh_sites(mock_site_response, etag, last_modified)
        
        assert cache.sites_cache_valid
        assert cache.get_sites_etag() == etag
        assert cache.get_sites_last_modified() == last_modified

    def test_list_all_sites(self, cache, mock_site_response):
        """Test listing all sites."""
        cache.refresh_sites(mock_site_response)
        
        sites = cache.list_all_sites()
        assert len(sites) == 2
        assert any(site.name == "Test Site 1" for site in sites)
        assert any(site.name == "Test Site 2" for site in sites)

    def test_check_for_site(self, cache, mock_site_response):
        """Test checking site existence."""
        cache.refresh_sites(mock_site_response)
        
        assert cache.check_for_site("Test Site 1")
        assert cache.check_for_site("test site 1")  # Case insensitive
        assert cache.check_for_site("  TEST  SITE  1  ")  # Whitespace normalization
        assert not cache.check_for_site("Nonexistent Site")

    def test_get_site(self, cache, mock_site_response):
        """Test getting site metadata."""
        cache.refresh_sites(mock_site_response)
        
        site = cache.get_site("Test Site 1")
        assert site is not None
        assert site.name == "Test Site 1"
        
        site_normalized = cache.get_site("test site 1")
        assert site_normalized is not None
        assert site_normalized.name == "Test Site 1"
        
        nonexistent = cache.get_site("Nonexistent Site")
        assert nonexistent is None

    def test_refresh_measurements(self, cache, mock_measurement_response):
        """Test refreshing measurements cache."""
        etag = '"def456"'
        last_modified = "Thu, 22 Oct 2015 08:28:00 GMT"
        
        cache.refresh_measurements(mock_measurement_response, etag, last_modified)
        
        assert cache.measurements_cache_valid
        assert cache.get_measurements_etag() == etag
        assert cache.get_measurements_last_modified() == last_modified

    def test_list_all_measurements(self, cache, mock_measurement_response):
        """Test listing all measurements."""
        cache.refresh_measurements(mock_measurement_response)
        
        measurements = cache.list_all_measurements()
        assert len(measurements) == 2
        assert any(m.name == "Flow" for m in measurements)
        assert any(m.name == "Water Level" for m in measurements)

    def test_get_measurements_for_site(self, cache, mock_measurement_response):
        """Test getting measurements for a specific site."""
        cache.refresh_measurements(mock_measurement_response)
        
        measurements = cache.get_measurements_for_site("Test Site 1")
        assert len(measurements) == 2
        
        measurements_normalized = cache.get_measurements_for_site("test site 1")
        assert len(measurements_normalized) == 2
        
        no_measurements = cache.get_measurements_for_site("Nonexistent Site")
        assert len(no_measurements) == 0

    def test_cache_expiry(self, cache, mock_site_response):
        """Test cache expiry functionality."""
        # Set very short TTL
        cache.default_ttl = timedelta(seconds=0.1)
        
        cache.refresh_sites(mock_site_response)
        assert cache.sites_cache_valid
        
        # Wait for expiry (simulate by manipulating the cache entry)
        import time
        time.sleep(0.2)
        cache._sites_cache_entry.expires = datetime.utcnow() - timedelta(seconds=1)
        
        assert not cache.sites_cache_valid

    def test_invalidation(self, cache, mock_site_response, mock_measurement_response):
        """Test cache invalidation."""
        cache.refresh_sites(mock_site_response)
        cache.refresh_measurements(mock_measurement_response)
        
        assert cache.sites_cache_valid
        assert cache.measurements_cache_valid
        
        cache.invalidate_sites()
        assert not cache.sites_cache_valid
        assert cache.measurements_cache_valid
        
        cache.refresh_sites(mock_site_response)
        cache.invalidate_measurements()
        assert cache.sites_cache_valid
        assert not cache.measurements_cache_valid
        
        cache.refresh_measurements(mock_measurement_response)
        cache.invalidate_all()
        assert not cache.sites_cache_valid
        assert not cache.measurements_cache_valid

    def test_ascii_folding(self):
        """Test ASCII folding in cache."""
        cache = DomainCache(ascii_fold=True)
        mock_response = Mock(spec=SiteListResponse)
        
        mock_site = Mock()
        mock_site.name = "Site Café"
        mock_response.site_list = [mock_site]
        
        cache.refresh_sites(mock_response)
        
        assert cache.check_for_site("Site Cafe")
        assert cache.check_for_site("site cafe")
        assert cache.get_site("site cafe") is not None