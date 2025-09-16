"""Shared fixtures for testing."""

import asyncio
import os
from pathlib import Path
import threading
import time

import pytest
from lxml import etree


def pytest_addoption(parser):
    """Add command line options for pytest."""
    parser.addoption(
        "--update",
        action="store_true",  # True if present, False if not
        default=False,
        help="Update the cached XML files with the latest data.",
    )
    parser.addoption(
        "--performance-local",
        action="store_true",
        default=False,
        help="Run performance tests against local FastAPI test server.",
    )
    parser.addoption(
        "--performance-remote",
        action="store_true",
        default=False,
        help="Run performance tests against remote internet-accessible server.",
    )


def pytest_configure(config):
    """Configure pytest with custom behavior."""
    # Mark performance tests to skip by default unless explicitly requested
    if not config.getoption("--performance-local") and not config.getoption("--performance-remote"):
        # Add skip marker for performance tests when not explicitly requested
        config.addinivalue_line(
            "markers", 
            "performance_local: skip unless --performance-local is specified"
        )
        config.addinivalue_line(
            "markers",
            "performance_remote: skip unless --performance-remote is specified"
        )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle performance test skipping."""
    skip_local = pytest.mark.skip(reason="Performance local tests require --performance-local flag")
    skip_remote = pytest.mark.skip(reason="Performance remote tests require --performance-remote flag")
    
    for item in items:
        if "performance_local" in item.keywords and not config.getoption("--performance-local"):
            item.add_marker(skip_local)
        if "performance_remote" in item.keywords and not config.getoption("--performance-remote"):
            item.add_marker(skip_remote)


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


@pytest.fixture(scope="session")
def local_test_server():
    """Start a local FastAPI test server for performance testing."""
    from tests.performance.local_server import create_test_server
    import threading
    import time
    import uvicorn
    import httpx
    
    # Configuration from environment variables
    host = "127.0.0.1"
    port = int(os.getenv("TEST_SERVER_PORT", "8001"))  # Use 8001 to avoid conflicts
    delay = float(os.getenv("TEST_SERVER_DELAY", "0.01"))  # Small default delay for testing
    error_rate = float(os.getenv("TEST_SERVER_ERROR_RATE", "0.0"))
    
    server = create_test_server(host=host, port=port, delay=delay, error_rate=error_rate)
    
    # Start server in a separate thread
    server_thread = threading.Thread(
        target=server.run,
        kwargs={"access_log": False},
        daemon=True
    )
    server_thread.start()
    
    # Wait for server to start
    server_url = f"http://{host}:{port}"
    max_retries = 50  # Increase retries
    for i in range(max_retries):
        try:
            response = httpx.get(f"{server_url}/health", timeout=2.0)
            if response.status_code == 200:
                break
        except (httpx.RequestError, httpx.TimeoutException):
            pass
        time.sleep(0.1)
    else:
        pytest.fail(f"Local test server failed to start after {max_retries * 0.1}s")
    
    yield {
        "base_url": server_url,
        "hts_endpoint": "foo.hts", 
        "host": host,
        "port": port,
        "delay": delay,
        "error_rate": error_rate
    }
    
    # Server cleanup happens automatically when thread ends


@pytest.fixture(scope="session") 
def performance_remote_client():
    """Create a remote client for performance testing."""
    from hurl.client import HilltopClient
    
    # Check if remote testing is enabled and environment is configured
    remote_base_url = os.getenv("HILLTOP_PERFORMANCE_BASE_URL")
    remote_hts_endpoint = os.getenv("HILLTOP_PERFORMANCE_HTS_ENDPOINT") 
    
    if not remote_base_url or not remote_hts_endpoint:
        pytest.skip(
            "Remote performance testing requires HILLTOP_PERFORMANCE_BASE_URL "
            "and HILLTOP_PERFORMANCE_HTS_ENDPOINT environment variables"
        )
    
    client = HilltopClient(
        base_url=remote_base_url,
        hts_endpoint=remote_hts_endpoint,
        timeout=30  # Longer timeout for performance tests
    )
    
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def performance_local_client(local_test_server):
    """Create a client configured for local performance testing."""
    from hurl.client import HilltopClient
    
    client = HilltopClient(
        base_url=local_test_server["base_url"],
        hts_endpoint=local_test_server["hts_endpoint"],
        timeout=30
    )
    
    try:
        yield client
    finally:
        client.close()
