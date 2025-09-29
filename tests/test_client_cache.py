from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from whurl.client import HilltopClient, AsyncHilltopClient
from whurl.schemas.responses.measurement_list import MeasurementListResponse
from whurl.schemas.responses.site_list import SiteListResponse
import pytest

"""Tests for client cache functionality."""




class TestHilltopClientCache:
    """Test cache functionality in HilltopClient."""

    @pytest.fixture
    def client(self):
        """Create a HilltopClient instance."""
        with patch('whurl.client.httpx.Client'):
            return HilltopClient(
                base_url="https://test.com",
                hts_endpoint="test.hts"
            )

    @pytest.fixture
    def mock_site_response(self):
        """Create a mock site list response."""
        mock_response = Mock(spec=SiteListResponse)
        
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
        
        mock_data_source = Mock()
        mock_data_source.site = "Test Site 1"
        
        mock_measurement1 = Mock()
        mock_measurement1.name = "Flow"
        mock_measurement1.units = "m³/s"
        
        mock_measurement2 = Mock()
        mock_measurement2.name = "Water Level"
        mock_measurement2.units = "m"
        
        mock_data_source.measurements = [mock_measurement1, mock_measurement2]
        mock_response.data_sources = [mock_data_source]
        return mock_response

    def test_list_all_sites_initial_fetch(self, client, mock_site_response):
        """Test list_all_sites fetches data on first call."""
        with patch.object(client, 'refresh_sites') as mock_refresh:
            client._domain_cache.refresh_sites(mock_site_response)
            
            sites = client.list_all_sites()
            
            assert len(sites) == 2
            assert any(site.name == "Test Site 1" for site in sites)

    def test_list_all_sites_uses_cache(self, client, mock_site_response):
        """Test list_all_sites uses cached data when valid."""
        # Pre-populate cache
        client._domain_cache.refresh_sites(mock_site_response)
        
        with patch.object(client, 'refresh_sites') as mock_refresh:
            sites = client.list_all_sites()
            
            # Should not call refresh since cache is valid
            mock_refresh.assert_not_called()
            assert len(sites) == 2

    def test_list_all_sites_force_refresh(self, client, mock_site_response):
        """Test list_all_sites forces refresh when requested."""
        # Pre-populate cache
        client._domain_cache.refresh_sites(mock_site_response)
        
        with patch.object(client, 'refresh_sites') as mock_refresh:
            sites = client.list_all_sites(refresh=True)
            
            # Should call refresh even though cache is valid
            mock_refresh.assert_called_once()

    def test_check_for_site(self, client, mock_site_response):
        """Test check_for_site functionality."""
        client._domain_cache.refresh_sites(mock_site_response)
        
        assert client.check_for_site("Test Site 1")
        assert client.check_for_site("test site 1")  # Case insensitive
        assert not client.check_for_site("Nonexistent Site")

    def test_check_for_site_with_refresh(self, client):
        """Test check_for_site with refresh when not found."""
        with patch.object(client, 'refresh_sites') as mock_refresh:
            result = client.check_for_site("Some Site", refresh=True)
            
            mock_refresh.assert_called_once()

    def test_get_site(self, client, mock_site_response):
        """Test get_site functionality."""
        client._domain_cache.refresh_sites(mock_site_response)
        
        site = client.get_site("Test Site 1")
        assert site is not None
        assert site.name == "Test Site 1"
        
        site_normalized = client.get_site("test site 1")
        assert site_normalized is not None
        assert site_normalized.name == "Test Site 1"
        
        nonexistent = client.get_site("Nonexistent Site")
        assert nonexistent is None

    def test_list_all_measurements(self, client, mock_measurement_response):
        """Test list_all_measurements functionality."""
        client._domain_cache.refresh_measurements(mock_measurement_response)
        
        measurements = client.list_all_measurements()
        assert len(measurements) == 2
        assert any(m.name == "Flow" for m in measurements)

    @patch('whurl.client.httpx.Response')
    @patch('whurl.client.SiteListResponse')
    def test_refresh_sites_basic(self, mock_response_class, mock_http_response, client):
        """Test basic refresh_sites functionality."""
        # Setup mocks
        mock_http_response.status_code = 200
        mock_http_response.headers = {'etag': '"abc123"', 'last-modified': 'Wed, 21 Oct 2015 07:28:00 GMT'}
        mock_http_response.text = '<xml>mock response</xml>'
        
        mock_site_response = Mock()
        mock_response_class.from_xml.return_value = mock_site_response
        
        client.session.get.return_value = mock_http_response
        
        # Test refresh
        client.refresh_sites()
        
        # Verify HTTP request was made
        client.session.get.assert_called_once()
        
        # Verify response was parsed
        mock_response_class.from_xml.assert_called_once_with('<xml>mock response</xml>')

    @patch('whurl.client.httpx.Response')
    def test_refresh_sites_with_conditional_headers(self, mock_http_response, client, mock_site_response):
        """Test refresh_sites with conditional request headers."""
        # Pre-populate cache with ETag and Last-Modified
        client._domain_cache.refresh_sites(
            mock_site_response, 
            etag='"old-etag"',
            last_modified="Wed, 20 Oct 2015 07:28:00 GMT"
        )
        
        mock_http_response.status_code = 200
        mock_http_response.headers = {}
        mock_http_response.text = '<xml>new response</xml>'
        
        client.session.get.return_value = mock_http_response
        
        with patch('whurl.client.SiteListResponse.from_xml') as mock_from_xml:
            client.refresh_sites()
            
            # Verify conditional headers were sent
            args, kwargs = client.session.get.call_args
            headers = kwargs.get('headers', {})
            assert 'If-None-Match' in headers
            assert 'If-Modified-Since' in headers
            assert headers['If-None-Match'] == '"old-etag"'

    @patch('whurl.client.httpx.Response')
    def test_refresh_sites_304_not_modified(self, mock_http_response, client, mock_site_response):
        """Test refresh_sites handles 304 Not Modified."""
        # Pre-populate cache
        client._domain_cache.refresh_sites(mock_site_response)
        original_timestamp = client._domain_cache._sites_cache_entry.timestamp
        
        mock_http_response.status_code = 304
        client.session.get.return_value = mock_http_response
        
        client.refresh_sites()
        
        # Cache should remain unchanged
        assert client._domain_cache._sites_cache_entry.timestamp == original_timestamp

    @patch('whurl.client.httpx.Response')
    @patch('whurl.client.MeasurementListResponse')
    def test_refresh_measurements_basic(self, mock_response_class, mock_http_response, client):
        """Test basic refresh_measurements functionality."""
        # Setup mocks
        mock_http_response.status_code = 200
        mock_http_response.headers = {'etag': '"def456"'}
        mock_http_response.text = '<xml>mock measurement response</xml>'
        
        mock_measurement_response = Mock()
        mock_response_class.from_xml.return_value = mock_measurement_response
        
        client.session.get.return_value = mock_http_response
        
        # Test refresh
        client.refresh_measurements()
        
        # Verify HTTP request was made
        client.session.get.assert_called_once()
        
        # Verify response was parsed
        mock_response_class.from_xml.assert_called_once_with('<xml>mock measurement response</xml>')


class TestAsyncHilltopClientCache:
    """Test cache functionality in AsyncHilltopClient."""

    @pytest.fixture
    def async_client(self):
        """Create an AsyncHilltopClient instance."""
        with patch('whurl.client.httpx.AsyncClient'):
            return AsyncHilltopClient(
                base_url="https://test.com",
                hts_endpoint="test.hts"
            )

    @pytest.fixture
    def mock_site_response(self):
        """Create a mock site list response."""
        mock_response = Mock(spec=SiteListResponse)
        
        mock_site1 = Mock()
        mock_site1.name = "Test Site 1"
        mock_site1.easting = 1234567.0
        mock_site1.northing = 7654321.0
        
        mock_response.site_list = [mock_site1]
        return mock_response

    @pytest.mark.asyncio
    async def test_async_list_all_sites(self, async_client, mock_site_response):
        """Test async list_all_sites functionality."""
        async_client._domain_cache.refresh_sites(mock_site_response)
        
        sites = await async_client.list_all_sites()
        assert len(sites) == 1
        assert sites[0].name == "Test Site 1"

    @pytest.mark.asyncio
    async def test_async_check_for_site(self, async_client, mock_site_response):
        """Test async check_for_site functionality."""
        async_client._domain_cache.refresh_sites(mock_site_response)
        
        assert await async_client.check_for_site("Test Site 1")
        assert not await async_client.check_for_site("Nonexistent Site")

    @pytest.mark.asyncio
    async def test_async_get_site(self, async_client, mock_site_response):
        """Test async get_site functionality."""
        async_client._domain_cache.refresh_sites(mock_site_response)
        
        site = await async_client.get_site("Test Site 1")
        assert site is not None
        assert site.name == "Test Site 1"

    @pytest.mark.asyncio
    async def test_async_refresh_sites(self, async_client):
        """Test async refresh_sites functionality."""
        mock_http_response = AsyncMock()
        mock_http_response.status_code = 200
        mock_http_response.headers = {'etag': '"abc123"'}
        mock_http_response.text = '<xml>mock response</xml>'
        
        async_client.session.get = AsyncMock(return_value=mock_http_response)
        
        with patch('whurl.client.SiteListResponse.from_xml') as mock_from_xml:
            mock_site_response = Mock()
            mock_from_xml.return_value = mock_site_response
            
            await async_client.refresh_sites()
            
            # Verify async HTTP request was made
            async_client.session.get.assert_called_once()
            
            # Verify response was parsed
            mock_from_xml.assert_called_once_with('<xml>mock response</xml>')

    @pytest.mark.asyncio
    async def test_async_refresh_measurements(self, async_client):
        """Test async refresh_measurements functionality."""
        mock_http_response = AsyncMock()
        mock_http_response.status_code = 200
        mock_http_response.headers = {'etag': '"def456"'}
        mock_http_response.text = '<xml>mock measurement response</xml>'
        
        async_client.session.get = AsyncMock(return_value=mock_http_response)
        
        with patch('whurl.client.MeasurementListResponse.from_xml') as mock_from_xml:
            mock_measurement_response = Mock()
            mock_from_xml.return_value = mock_measurement_response
            
            await async_client.refresh_measurements()
            
            # Verify async HTTP request was made
            async_client.session.get.assert_called_once()
            
            # Verify response was parsed
            mock_from_xml.assert_called_once_with('<xml>mock measurement response</xml>')