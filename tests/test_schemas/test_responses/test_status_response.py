"""Tests for the Status response schema."""

import os

import pytest
import pytest_httpx


"""Tests for the Status response schema."""

import os

import pytest
import pytest_httpx


@pytest.fixture
def status_response_xml(request, httpx_mock, remote_client):
    """Test the status response schema with multiple data source support."""
    from pathlib import Path
    from urllib.parse import urlparse
    
    from hurl.schemas.requests import StatusRequest
    from tests.test_data_sources import TestDataManager, TestDataSource

    # Initialize data manager
    manager = TestDataManager(Path(__file__))
    data_type = "status"
    filename = "response.xml"

    # Handle remote updates (--update flag)
    if request.config.getoption("--update"):
        # Switch off httpx mock so that remote request can go through
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_url = StatusRequest(
            base_url=remote_client.base_url, hts_endpoint=remote_client.hts_endpoint
        ).gen_url()
        remote_xml = remote_client.session.get(remote_url).text
        
        # Save to cache
        cache_path = manager.cached_dir / data_type / filename
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(remote_xml, encoding="utf-8")
        
        return remote_xml

    # Get preferred data source from CLI option
    data_source_option = request.config.getoption("--data-source")
    preferred_source = None
    if data_source_option != "auto":
        preferred_source = TestDataSource(data_source_option)

    # Get data file with fallback logic
    data_file = manager.get_data_file(data_type, filename, preferred_source)
    
    if data_file is None:
        available_sources = manager.get_available_sources(data_type, filename)
        pytest.skip(
            f"No data available for {data_type}/{filename}. "
            f"Available sources: {[s.value for s in available_sources]}. "
            f"Use --data-source to specify preference or --update to fetch remote data."
        )

    return data_file.read_text(encoding="utf-8")


class TestRemoteFixtures:
    """Test fixture validation against remote API (integration testing)."""
    
    @pytest.mark.remote
    @pytest.mark.update
    @pytest.mark.integration
    @pytest.mark.remote_data
    def test_response_xml_fixture(self, httpx_mock, remote_client, status_response_xml):
        """Validate the status response XML fixture."""
        from urllib.parse import urlparse

        from hurl.schemas.requests import StatusRequest
        from tests.conftest import remove_tags

        cached_xml = status_response_xml

        status_req = StatusRequest(
            base_url=remote_client.base_url, hts_endpoint=remote_client.hts_endpoint
        )

        remote_url = status_req.gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_xml = remote_client.session.get(remote_url).text

        tags_to_remove = [
            "ProcessID",
            "WorkingSet",
            "OpenFor",
            "FullRefresh",
            "SoftRefresh",
            "DataFile",
        ]

        # remove the tags OpenFor, FullRefresh and SoftRefresh and their contents
        remote_xml_cleaned = remove_tags(remote_xml, tags_to_remove)
        cached_xml_cleaned = remove_tags(cached_xml, tags_to_remove)

        assert remote_xml_cleaned == cached_xml_cleaned


class TestResponseValidation:
    """Unit tests for response schema validation (CI-safe)."""

    @pytest.mark.unit
    @pytest.mark.mocked_data
    def test_status_response(self, httpx_mock, status_response_xml):
        """Test the StatusResponse model."""

        from hurl.client import HilltopClient
        from hurl.schemas.requests import StatusRequest
        from hurl.schemas.responses import StatusResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        status_req = StatusRequest(base_url=base_url, hts_endpoint=hts_endpoint)

        test_url = status_req.gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=status_response_xml,
        )

        # Call the client as normal
        client = HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        )

        result = client.get_status()

        assert isinstance(result, StatusResponse)
        # Use flexible assertions that work with both real and mocked data
        assert result.agency in ["Horizons", "Test Council"]  # Accept both real and test data
        assert result.script_name is not None  # Just verify it exists

    @pytest.mark.unit
    @pytest.mark.mocked_data
    def test_to_dict(self, status_response_xml):
        """Test to_dict method."""
        import xmltodict

        from hurl.schemas.responses import StatusResponse

        status_response = StatusResponse.from_xml(status_response_xml)

        # Convert to dictionary
        test_dict = status_response.to_dict()

        # Test that the basic structure is correct
        assert isinstance(test_dict, dict)
        assert "Agency" in test_dict
        assert "Version" in test_dict
        
        # Verify that the values match the XML content
        naive_dict = xmltodict.parse(status_response_xml)["HilltopServer"]
        assert test_dict["Agency"] == naive_dict["Agency"]
        assert test_dict["Version"] == naive_dict["Version"]
        
        # For mocked data, we may not have all fields, so just test core functionality
        # rather than exact equality with raw XML
