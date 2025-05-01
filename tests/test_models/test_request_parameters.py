"""Test the HilltopRequestParameters class."""

import pytest

from hurl.exceptions import HilltopHTTPError
from hurl.models.request_parameters import HilltopRequestParameters


class TestHilltopRequestParameters:
    def test_correct_url(self):
        """Test the correct URL."""
        params = HilltopRequestParameters(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            service="Hilltop",
            request="Status",
        )
        assert params.base_url == "http://example.com"
        assert params.hts_endpoint == "foo.hts"
        assert params.service == "Hilltop"
        assert params.request == "Status"

    @pytest.mark.xfail(raises=HilltopHTTPError, strict=True)
    def test_invalid_base_url(self):
        """Test the invalid base URL."""
        HilltopRequestParameters(
            base_url="Not a url",
            hts_endpoint="foo.hts",
            service="Hilltop",
            request="Status",
        )

    @pytest.mark.xfail(raises=HilltopHTTPError, strict=True)
    def test_invalid_hts_endpoint(self):
        """Test the invalid HTS endpoint."""
        HilltopRequestParameters(
            base_url="http://example.com",
            hts_endpoint="Not an hts file",
            service="Hilltop",
            request="Status",
        )

    @pytest.mark.xfail(raises=HilltopHTTPError, strict=True)
    def test_invalid_service(self):
        """Test the invalid service name."""
        req = HilltopRequestParameters(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            service="Not Hilltop",
            request="Status",
        )

    @pytest.mark.xfail(raises=HilltopHTTPError, strict=True)
    def test_invalid_request(self):
        """Test the invalid request name."""
        HilltopRequestParameters(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            service="Hilltop",
            request="Not a valid request",
        )
