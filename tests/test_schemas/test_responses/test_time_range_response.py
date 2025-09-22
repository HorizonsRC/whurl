"""Test the TimeRange Response Schema."""

import os

import pytest
from dotenv import load_dotenv

load_dotenv()


def create_cached_fixtures(filename: str, request_kwargs: dict = None):
    """Factory to create cached fixtures."""

    @pytest.fixture
    def fixture_func(request, httpx_mock, remote_client):
        """Load test XML once per test session."""
        from pathlib import Path
        from urllib.parse import urlparse

        from whurl.schemas.requests.time_range import TimeRangeRequest

        path = (
            Path(__file__).parent.parent.parent
            / "fixture_cache"
            / "time_range"
            / filename
        )
        if request.config.getoption("--update"):
            # Switch off httpx mock so that cached request can go through.
            httpx_mock._options.should_mock = (
                lambda request: request.url.host
                != urlparse(remote_client.base_url).netloc
            )
            cached_url = TimeRangeRequest(
                base_url=remote_client.base_url,
                hts_endpoint=remote_client.hts_endpoint,
                **(request_kwargs or {}),
            ).gen_url()
            cached_xml = remote_client.session.get(cached_url).text
            path.write_text(cached_xml, encoding="utf-8")
        raw_xml = path.read_text(encoding="utf-8")
        return raw_xml

    return fixture_func


def create_mocked_fixtures(filename: str):
    """Factory to create mocked fixtures."""

    @pytest.fixture
    def fixture_func():
        """Load test XML once per test session."""
        from pathlib import Path

        path = (
            Path(__file__).parent.parent.parent
            / "mocked_data"
            / "time_range"
            / filename
        )
        raw_xml = path.read_text(encoding="utf-8")
        return raw_xml

    return fixture_func


# Create cached fixtures
basic_response_xml_cached = create_cached_fixtures(
    "response.xml",
    {"site": os.getenv("TEST_SITE"), "measurement": os.getenv("TEST_MEASUREMENT")},
)

# Create mocked fixtures
basic_response_xml_mocked = create_mocked_fixtures("response.xml")


class TestRemoteFixtures:
    @pytest.mark.remote
    @pytest.mark.integration
    def test_basic_response_xml_fixture(
        self,
        remote_client,
        httpx_mock,
        basic_response_xml_cached,
    ):
        """Test that the basic response XML fixture is loaded correctly."""
        from urllib.parse import urlparse

        from whurl.schemas.requests.time_range import TimeRangeRequest
        from tests.conftest import remove_tags

        # Generate the URL for the remote request.
        remote_url = TimeRangeRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site=os.getenv("TEST_SITE"),
            measurement=os.getenv("TEST_MEASUREMENT"),
        ).gen_url()
        print(remote_url)
        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_xml = remote_client.session.get(remote_url).text

        tags_to_remove = [
            "From",
            "To",
        ]

        remote_xml_cleaned = remove_tags(remote_xml, tags_to_remove)
        response_xml_cleaned = remove_tags(basic_response_xml_cached, tags_to_remove)

        assert remote_xml_cleaned == response_xml_cleaned


class TestTimeRangeResponse:
    @pytest.mark.unit
    def test_time_range_response_unit(self, httpx_mock, basic_response_xml_mocked):
        """Test the TimeRange Response Schema with mocked data."""

        from datetime import datetime

        from whurl.client import HilltopClient
        from whurl.schemas.requests.time_range import TimeRangeRequest
        from whurl.schemas.responses.time_range import TimeRangeResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = TimeRangeRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="Test Site Alpha",
            measurement="Test Measurement",
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=basic_response_xml_mocked,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            response = client.get_time_range(
                site="Test Site Alpha",
                measurement="Test Measurement",
            )

        assert isinstance(response, TimeRangeResponse)
        assert isinstance(response.site, str)
        assert isinstance(response.to_time, datetime)
        assert isinstance(response.from_time, datetime)

    @pytest.mark.integration
    def test_time_range_response_integration(
        self, httpx_mock, basic_response_xml_cached
    ):
        """Test the TimeRange Response Schema with cached data."""

        from datetime import datetime

        from whurl.client import HilltopClient
        from whurl.schemas.requests.time_range import TimeRangeRequest
        from whurl.schemas.responses.time_range import TimeRangeResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = TimeRangeRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site=os.getenv("TEST_SITE"),
            measurement=os.getenv("TEST_MEASUREMENT"),
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=basic_response_xml_cached,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            response = client.get_time_range(
                site=os.getenv("TEST_SITE"),
                measurement=os.getenv("TEST_MEASUREMENT"),
            )

        assert isinstance(response, TimeRangeResponse)
        assert isinstance(response.site, str)
        assert isinstance(response.to_time, datetime)
        assert isinstance(response.from_time, datetime)
