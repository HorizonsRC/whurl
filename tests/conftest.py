"""Shared fixtures for testing."""

from pathlib import Path

import pytest
from lxml import etree

from hurl.models.measurement_list import HilltopMeasurementList


def pytest_addoption(parser):
    """Add command line options for pytest."""
    parser.addoption(
        "--update",
        action="store_true",  # True if present, False if not
        default=False,
        help="Update the cached XML files with the latest data.",
    )


def remove_tags(xml_str, tags_to_remove):
    """Shared XML cleaning utility."""
    root = etree.fromstring(xml_str)
    for tag in tags_to_remove:
        for element in root.xpath(f".//{tag}"):
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)
    return etree.tostring(root, encoding='unicode')


@pytest.fixture(scope="session")
def remote_client():
    """Create a remote client for testing."""
    from hurl.client import HilltopClient

    client = HilltopClient()

    try:
        yield client
    finally:
        client.session.close()


@pytest.fixture
def mock_hilltop_client_factory(mocker):
    """Mock HilltopClient Factory for testing."""

    def _factory(response_xml="<default>payload</default>", status_code=200):
        # Mock the response
        mock_response = mocker.MagicMock()
        mock_response.text = response_xml
        mock_response.status_code = status_code

        # Mock the session
        mock_session = mocker.MagicMock()
        mock_session.get.return_value = mock_response

        # Mock the client context manager
        mock_client = mocker.MagicMock()
        mock_client.base_url = "http://example.com"
        mock_client.hts_endpoint = "foo.hts"
        mock_client.timeout = 60
        mock_client.__enter__.return_value = mock_client  # Returns self
        mock_client.__exit__.return_value = None
        mock_client.session = mock_session

        # Patch the real client
        mocker.patch("hurl.client.HilltopClient", return_value=mock_client)

        return {
            "client": mock_client,
            "session": mock_session,
            "response": mock_response,
        }
    return _factory
