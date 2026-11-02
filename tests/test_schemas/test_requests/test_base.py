"""Tests for the base request schema."""

import pytest

from whurl.exceptions import HilltopRequestError
from whurl.schemas.requests import GetDataRequest, StatusRequest



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


# -----------------------------------------------------------------------------
# Test for those extra slashes
# 
# ``gen_url`` builds ``f"{base_url}/{hts_endpoint}?..."``. If the configured
# base URL already ends in ``/`` (very common when it is copied from a browser
# or a .env file) the result has a double slash:
#   
#   http://server//RawLoggerNet.hts?Service=Hilltop...
#
# Some servers tolerate that and some do not, and either way it makes the URL
# that gets pasted into a browser look wrong. The same happens if the endpoint
# starts with ``/``.
# 
# The rule: however the two parts are written, the URL has one slash between
# them, and any path already in the base URL is kept.
# -----------------------------------------------------------------------------

EXPECTED_START = "https://example.com/test.hts?"


def url_for(base_url: str, hts_endpoint: str) -> str:
    return StatusRequest(base_url=base_url, hts_endpoint=hts_endpoint).gen_url()


@pytest.mark.unit
class TestSingleSlash:
    @pytest.mark.parametrize(
        "base_url",
        [
            "https://example.com",
            "https://example.com/",
            "https://example.com//",
        ],
    )
    def test_trailing_slashes_on_the_base_url_do_not_double_up(self, base_url):
        assert url_for(base_url, "test.hts").startswith(EXPECTED_START)
    
    @pytest.mark.parametrize("hts_endpoint", ["test.hts", "/test.hts", "//test.hts"])
    def test_leading_slashing_on_the_endpoint_do_not_double_up(self, hts_endpoint):
        assert url_for("https://example.com", hts_endpoint).startswith(
            EXPECTED_START
        )

    def test_both_at_once(self):
        assert url_for("https://example.com/", "/test.hts").startswith(
            EXPECTED_START
        )

    def test_surrounding_whitespace_is_ignored(self):
        # Easy to pick up from a .env file or a copy-paste.
        assert url_for(" https://example.com/ ", " test.hts ").startswith(
            EXPECTED_START
        )


@pytest.mark.unit
class TestPathsAreKept:
    def test_a_path_in_the_base_url_is_kept(self):
        # Not sure if Hilltop Server even allows this.
        url = url_for("https://example.com/hilltop/", "test.hts")

        assert url.startswith("https://example.com/hilltop/test.hts?")


    def test_a_directory_in_the_endpoint_is_kept(self):
        url = url_for("https://example.com", "data/test.hts")

        assert url.startswith("https://example.com/data/test.hts?")


    def test_the_port_is_kept(self):
        url = url_for("http://localhost:8080/", "test.hts")

        assert url.startswith("http://localhost:8080/test.hts?")


@pytest.mark.unit
class TestOtherRequestTypes:
    def test_get_data_requests_join_the_same_way(self):
        url = GetDataRequest(
                base_url="https://example.com/",
                hts_endpoint="/test.hts",
                site="Test Site Alpha",
                measurement="Stage",
            ).gen_url()

        assert url.startswith(EXPECTED_START)
        assert "//test.hts" not in url


@pytest.mark.unit
class TestValidationStillWorks:
    def test_a_base_url_with_no_scheme_is_still_rejected(self):
        with pytest.raises(HilltopRequestError):
            url_for("example.com/", "test.hts")


    def test_an_endpoint_not_ending_in_hts_is_still_rejected(self):
        with pytest.raises(HilltopRequestError):
            url_for("https://example.com", "/test.txt")


    def test_a_slash_only_base_url_is_still_rejected(self):
        with pytest.raises(HilltopRequestError):
            url_for("/", "test.hts")
