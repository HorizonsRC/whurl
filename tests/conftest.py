"""Shared fixtures for testing."""

import pytest
from pathlib import Path
from hurl.models.measurement_list import HilltopMeasurementList


def pytest_addoption(parser):
    """Add command line options for pytest."""
    parser.addoption(
        "--update",
        action="store_true",  # True if present, False if not
        default=False,
        help="Update the cached XML files with the latest data.",
    )


@pytest.fixture(scope="session")
def remote_client():
    """Create a remote client for testing."""
    from hurl.client import HilltopClient

    client = HilltopClient()

    try:
        yield client
    finally:
        client.session.close()
