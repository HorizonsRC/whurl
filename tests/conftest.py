"""Shared fixtures for testing."""

from pathlib import Path

import pytest
from dotenv import load_dotenv
from lxml import etree

load_dotenv()


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line(
        "markers", "remote: mark test as requiring remote API access"
    )
    config.addinivalue_line("markers", "update: mark test as updating cached fixtures")
    config.addinivalue_line("markers", "performance: mark test as a performance test")


def pytest_addoption(parser):
    """Add command line options for pytest."""
    parser.addoption(
        "--mode",
        action="store",
        choices=["all", "offline", "unit", "integration", "performance"],
        default="offline",
        help="Select the type of tests to run (default: all tests)",
    )

    parser.addoption(
        "--update",
        action="store_true",  # True if present, False if not
        default=False,
        help=(
            "Update the cached XML files with the latest data. "
            "Only used with --integration or --all."
        ),
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle performance test skipping."""
    import os

    # Check for required environment variables when running integration tests
    if config.getoption("--mode") in ["integration", "all"] or config.getoption(
        "--update"
    ):
        required_env_vars = [
            "TEST_SITE",
            "TEST_MEASUREMENT",
            "TEST_AGENCY",
            "TEST_COLLECTION",
        ]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise pytest.PytestConfigWarning(
                "Integration tests require environment variables: "
                f"{', '.join(missing_vars)}. "
                "Please set these in a .env file or environment."
            )

    for item in items:
        if config.getoption("--mode") == "offline":
            if "remote" in item.keywords:
                item.add_marker(
                    pytest.mark.skip(reason="Skipping online tests in offline mode")
                )
        if config.getoption("--mode") == "unit":
            if "integration" in item.keywords or "performance" in item.keywords:
                item.add_marker(
                    pytest.mark.skip(reason="Only running unit tests in unit mode")
                )
        if config.getoption("--mode") == "integration":
            if "unit" in item.keywords or "performance" in item.keywords:
                item.add_marker(
                    pytest.mark.skip(
                        reason="Only running integration tests in unit mode"
                    )
                )
        if config.getoption("--mode") == "performance":
            raise pytest.PytestConfigWarning(
                "Performance tests are not yet implemented."
            )

        if config.getoption("--update"):
            if config.getoption("--mode") not in ["all", "integration"]:
                raise pytest.PytestConfigWarning(
                    "--update can only be used with --mode=all or --mode=integration"
                )
            if config.getoption("--mode") == "offine":
                raise pytest.PytestConfigWarning(
                    "--update requires remote access, "
                    "cannot be used with --mode=offline"
                )


def remove_tags(xml_str, tags_to_remove):
    """Shared XML cleaning utility."""
    root = etree.fromstring(xml_str)
    for tag in tags_to_remove:
        for element in root.xpath(f".//{tag}"):
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)
    return etree.tostring(root, encoding="unicode")


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
