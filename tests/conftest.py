"""Shared fixtures for testing."""

import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def sample_measurement_list_multi_response_xml():
    """Load test XML once per test session."""
    path = Path(__file__).parent / "fixtures" / "measurement_list_multi_response.xml"
    raw_xml = path.read_text(encoding="utf-8")

    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def remote_client():
    """Create a remote client for testing."""
    from hurl.client import HilltopClient

    with HilltopClient() as client:
        yield client
