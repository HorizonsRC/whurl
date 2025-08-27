"""Tests for the request property on response objects."""

from unittest.mock import Mock, patch

import pytest

from hurl.client import HilltopClient
from hurl.schemas.requests import (
    GetDataRequest, MeasurementListRequest, SiteInfoRequest,
    SiteListRequest, StatusRequest, CollectionListRequest, TimeRangeRequest
)
from hurl.schemas.responses import (
    GetDataResponse, MeasurementListResponse, SiteInfoResponse,
    SiteListResponse, StatusResponse, CollectionListResponse, TimeRangeResponse
)


class TestRequestProperty:
    """Test the request property functionality on response objects."""
    
    def test_response_request_property_basic(self):
        """Test that response objects can have a request property set."""
        request = GetDataRequest(
            base_url="https://example.com",
            hts_endpoint="test.hts",
            site="Test Site",
            measurement="Temperature"
        )
        
        response = GetDataResponse(agency="Test Agency")
        response.request = request
        
        assert response.request is not None
        assert response.request.site == "Test Site"
        assert response.request.measurement == "Temperature"
        assert "Site=Test%20Site" in response.request.gen_url()
    
    @pytest.mark.parametrize("response_class,request_class,response_data,request_data", [
        (GetDataResponse, GetDataRequest, {"agency": "Test"}, {"site": "Test Site"}),
        (MeasurementListResponse, MeasurementListRequest, {"agency": "Test"}, {"site": "Test Site"}),
        (SiteInfoResponse, SiteInfoRequest, {"agency": "Test"}, {"site": "Test Site"}),
        (SiteListResponse, SiteListRequest, {"agency": "Test"}, {}),
        (StatusResponse, StatusRequest, {"agency": "Test"}, {}),
        (CollectionListResponse, CollectionListRequest, {"title": "Test"}, {}),
    ])
    def test_all_response_classes_support_request_property(
        self, response_class, request_class, response_data, request_data
    ):
        """Test that all response classes support the request property."""
        request = request_class(
            base_url="https://example.com",
            hts_endpoint="test.hts",
            **request_data
        )
        
        response = response_class(**response_data)
        response.request = request
        
        assert response.request is not None
        assert response.request.base_url == "https://example.com"
        assert response.request.hts_endpoint == "test.hts"
        assert "https://example.com/test.hts" in response.request.gen_url()
    
    def test_client_sets_request_property(self):
        """Test that the client sets the request property on responses."""
        client = HilltopClient(
            base_url="https://api.example.com",
            hts_endpoint="test.hts"
        )
        
        # Mock XML response
        mock_response_xml = """<?xml version="1.0"?>
<Hilltop>
    <Agency>Test Agency</Agency>
</Hilltop>"""
        
        mock_response = Mock()
        mock_response.text = mock_response_xml
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        with patch.object(client.session, 'get', return_value=mock_response):
            response = client.get_data(site="Test Site", measurement="Temperature")
            
            # Verify the request property is set by the client
            assert response.request is not None
            assert response.request.site == "Test Site"
            assert response.request.measurement == "Temperature"
            assert response.request.base_url == "https://api.example.com"
            assert response.request.hts_endpoint == "test.hts"
            
            # Verify URL can be generated for debugging/logging
            url = response.request.gen_url()
            assert "Site=Test%20Site" in url
            assert "Measurement=Temperature" in url
    
    def test_usage_example_from_issue(self):
        """Test the exact usage example provided in the GitHub issue."""
        client = HilltopClient(
            base_url="https://api.example.com",
            hts_endpoint="resource.hts"
        )
        
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0"?><Hilltop><Agency>Test</Agency></Hilltop>"""
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        with patch.object(client.session, 'get', return_value=mock_response):
            # This is the usage example from the issue
            response = client.get_data(site="test-site", measurement="water-level")
            
            # This is what developers can now do for debugging/logging
            debug_url = response.request.gen_url()  # Access the actual URL used
            
            assert "api.example.com/resource.hts" in debug_url
            assert "Site=test-site" in debug_url
            assert "Measurement=water-level" in debug_url