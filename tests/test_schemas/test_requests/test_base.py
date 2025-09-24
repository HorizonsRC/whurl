"""Tests for the base request schema."""

import pytest


def test_validate_base_url():
    """Test base_url validation."""
    from whurl.exceptions import HilltopRequestError
    from whurl.schemas.requests.base import BaseHilltopRequest

    # Valid URL
    valid_request = BaseHilltopRequest(
        base_url="https://example.com", hts_endpoint="test.hts"
    )
    assert valid_request.base_url == "https://example.com"

    # Invalid URL
    with pytest.raises(HilltopRequestError):
        BaseHilltopRequest(base_url="invalid-url", hts_endpoint="test.hts")


def test_validate_hts_endpoint():
    """Test hts_endpoint validation."""
    from whurl.exceptions import HilltopRequestError
    from whurl.schemas.requests.base import BaseHilltopRequest

    # Valid HTS endpoint
    valid_request = BaseHilltopRequest(
        base_url="https://example.com", hts_endpoint="test.hts"
    )
    assert valid_request.hts_endpoint == "test.hts"
    # Invalid HTS endpoint
    with pytest.raises(HilltopRequestError):
        BaseHilltopRequest(base_url="https://example.com", hts_endpoint="invalid.txt")


def test_validate_service():
    """Test service validation."""
    from whurl.exceptions import HilltopRequestError
    from whurl.schemas.requests.base import BaseHilltopRequest

    # Valid service
    valid_request = BaseHilltopRequest(
        base_url="https://example.com", hts_endpoint="test.hts", service="Hilltop"
    )
    assert valid_request.service == "Hilltop"
    # Invalid service: empty
    with pytest.raises(HilltopRequestError):
        BaseHilltopRequest(
            base_url="https://example.com", hts_endpoint="test.hts", service=None
        )
    # Invalid service: unsupported
    with pytest.raises(HilltopRequestError):
        BaseHilltopRequest(
            base_url="https://example.com", hts_endpoint="test.hts", service="SOS"
        )
    with pytest.raises(HilltopRequestError):
        BaseHilltopRequest(
            base_url="https://example.com", hts_endpoint="test.hts", service="WFS"
        )
    with pytest.raises(HilltopRequestError):
        BaseHilltopRequest(
            base_url="https://example.com",
            hts_endpoint="test.hts",
            service="UnknownService",
        )


def test_validate_request():
    """Test request validation."""
    from whurl.exceptions import HilltopRequestError
    from whurl.schemas.requests.base import BaseHilltopRequest

    # Valid request
    valid_request = BaseHilltopRequest(
        base_url="https://example.com", hts_endpoint="test.hts", request="Status"
    )
    assert valid_request.request == "Status"

    # Invalid request: empty
    with pytest.raises(HilltopRequestError):
        BaseHilltopRequest(
            base_url="https://example.com", hts_endpoint="test.hts", request=None
        )
    # Invalid request: unsupported
    with pytest.raises(HilltopRequestError):
        BaseHilltopRequest(
            base_url="https://example.com",
            hts_endpoint="test.hts",
            request="InvalidRequest",
        )
