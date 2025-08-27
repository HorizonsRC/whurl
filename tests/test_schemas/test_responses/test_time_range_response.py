"""Test the TimeRange Response Schema."""

import pytest


@pytest.fixture
def basic_response_xml(request, httpx_mock, remote_client):
    """Load test XML once per test session."""
    from pathlib import Path
    from urllib.parse import urlparse

    from hurl.schemas.requests.time_range import TimeRangeRequest

    path = (
        Path(__file__).parent.parent.parent
        / "fixture_cache"
        / "time_range"
        / "response.xml"
    )

    if request.config.getoption("--update"):
        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )
        remote_url = TimeRangeRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site="Manawatu at Teachers College",
            measurement="Stage",
        ).gen_url()
        remote_xml = remote_client.session.get(remote_url).text

        path.write_text(remote_xml, encoding="utf-8")

    raw_xml = path.read_text(encoding="utf-8")

    return raw_xml


class TestRemoteFixtures:
    @pytest.mark.remote
    @pytest.mark.update
    def test_basic_response_xml_fixture(
        self,
        remote_client,
        httpx_mock,
        basic_response_xml,
    ):
        """Test that the basic response XML fixture is loaded correctly."""
        from urllib.parse import urlparse

        from hurl.schemas.requests.time_range import TimeRangeRequest
        from tests.conftest import remove_tags

        # Generate the URL for the remote request.
        remote_url = TimeRangeRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site="Manawatu at Teachers College",
            measurement="Stage",
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
        response_xml_cleaned = remove_tags(basic_response_xml, tags_to_remove)

        assert remote_xml_cleaned == response_xml_cleaned


class TestTimeRangeResponse:
    def test_time_range_response(self, httpx_mock, basic_response_xml):
        """Test the TimeRange Response Schema."""

        from datetime import datetime

        from hurl.client import HilltopClient
        from hurl.schemas.requests.time_range import TimeRangeRequest
        from hurl.schemas.responses.time_range import TimeRangeResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = TimeRangeRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="Manawatu at Teachers College",
            measurement="Stage",
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=basic_response_xml,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            response = client.get_time_range(
                site="Manawatu at Teachers College",
                measurement="Stage",
            )

        assert isinstance(response, TimeRangeResponse)
        assert isinstance(response.site, str)
        assert isinstance(response.to_time, datetime)
        assert isinstance(response.from_time, datetime)
