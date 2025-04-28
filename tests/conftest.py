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
